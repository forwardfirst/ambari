"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""
import os.path
import time

from resource_management.core import shell
from resource_management.core.source import Template
from resource_management.core.resources.system import File, Execute, Directory
from resource_management.core.resources.service import Service
from resource_management.libraries.functions.format import format
from resource_management.libraries.functions.check_process_status import check_process_status
from resource_management.libraries.resources.execute_hadoop import ExecuteHadoop
from resource_management.libraries.functions import Direction
from ambari_commons import OSCheck, OSConst
from ambari_commons.os_family_impl import OsFamilyImpl, OsFamilyFuncImpl
from utils import get_dfsadmin_base_command

if OSCheck.is_windows_family():
  from resource_management.libraries.functions.windows_service_utils import check_windows_service_status

from resource_management.core.shell import as_user
from resource_management.core.exceptions import Fail
from resource_management.core.logger import Logger

from utils import service, safe_zkfc_op, is_previous_fs_image
from setup_ranger_hdfs import setup_ranger_hdfs, create_ranger_audit_hdfs_directories


@OsFamilyFuncImpl(os_family=OsFamilyImpl.DEFAULT)
def namenode(action=None, hdfs_binary=None, do_format=True, upgrade_type=None, env=None):
  if action is None:
    raise Fail('"action" parameter is required for function namenode().')

  if action in ["start", "stop"] and hdfs_binary is None:
    raise Fail('"hdfs_binary" parameter is required for function namenode().')

  if action == "configure":
    import params
    #we need this directory to be present before any action(HA manual steps for
    #additional namenode)
    create_name_dirs(params.dfs_name_dir)
  elif action == "start":
    Logger.info("Called service {0} with upgrade_type: {1}".format(action, str(upgrade_type)))
    setup_ranger_hdfs(upgrade_type=upgrade_type)
    import params
    if do_format and not params.hdfs_namenode_format_disabled:
      format_namenode()
      pass

    File(params.exclude_file_path,
         content=Template("exclude_hosts_list.j2"),
         owner=params.hdfs_user,
         group=params.user_group
    )

    if params.dfs_ha_enabled and \
      params.dfs_ha_namenode_standby is not None and \
      params.hostname == params.dfs_ha_namenode_standby:
        # if the current host is the standby NameNode in an HA deployment
        # run the bootstrap command, to start the NameNode in standby mode
        # this requires that the active NameNode is already up and running,
        # so this execute should be re-tried upon failure, up to a timeout
        success = bootstrap_standby_namenode(params)
        if not success:
          raise Fail("Could not bootstrap standby namenode")

    if upgrade_type == "rolling" and params.dfs_ha_enabled:
      # Most likely, ZKFC is up since RU will initiate the failover command. However, if that failed, it would have tried
      # to kill ZKFC manually, so we need to start it if not already running.
      safe_zkfc_op(action, env)

    options = ""
    if upgrade_type == "rolling":
      if params.upgrade_direction == Direction.UPGRADE:
        options = "-rollingUpgrade started"
      elif params.upgrade_direction == Direction.DOWNGRADE:
        options = "-rollingUpgrade downgrade"
        
    elif upgrade_type == "nonrolling":
      is_previous_image_dir = is_previous_fs_image()
      Logger.info(format("Previous file system image dir present is {is_previous_image_dir}"))

      if params.upgrade_direction == Direction.UPGRADE:
        options = "-rollingUpgrade started"
      elif params.upgrade_direction == Direction.DOWNGRADE:
        options = "-rollingUpgrade downgrade"

    Logger.info(format("Option for start command: {options}"))

    service(
      action="start",
      name="namenode",
      user=params.hdfs_user,
      options=options,
      create_pid_dir=True,
      create_log_dir=True
    )

    if params.security_enabled:
      Execute(format("{kinit_path_local} -kt {hdfs_user_keytab} {hdfs_principal_name}"),
              user = params.hdfs_user)
    dfsadmin_base_command = get_dfsadmin_base_command(hdfs_binary, use_specific_namenode=True)
    is_namenode_safe_mode_off = dfsadmin_base_command + " -safemode get | grep 'Safe mode is OFF'"
    if params.dfs_ha_enabled:
      is_active_namenode_cmd = as_user(format("{hdfs_binary} --config {hadoop_conf_dir} haadmin -getServiceState {namenode_id} | grep active"), params.hdfs_user, env={'PATH':params.hadoop_bin_dir})
    else:
      is_active_namenode_cmd = True
    
    # During NonRolling Upgrade, both NameNodes are initially down,
    # so no point in checking if this is the active or standby.
    if upgrade_type == "nonrolling":
      is_active_namenode_cmd = False

    # ___Scenario___________|_Expected safemode state__|_Wait for safemode OFF____|
    # no-HA                 | ON -> OFF                | Yes                      |
    # HA and active         | ON -> OFF                | Yes                      |
    # HA and standby        | no change                | no check                 |
    # RU with HA on active  | ON -> OFF                | Yes                      |
    # RU with HA on standby | ON -> OFF                | Yes                      |
    # EU with HA on active  | no change                | no check                 |
    # EU with HA on standby | no change                | no check                 |
    # EU non-HA             | no change                | no check                 |

    check_for_safemode_off = False
    msg = ""
    if params.dfs_ha_enabled:
      if upgrade_type is not None:
        check_for_safemode_off = True
        msg = "Must wait to leave safemode since High Availability is enabled during a Stack Upgrade"
      else:
        Logger.info("Wait for NameNode to become active.")
        if is_active_namenode(hdfs_binary): # active
          check_for_safemode_off = True
          msg = "Must wait to leave safemode since High Availability is enabled and this is the Active NameNode."
        else:
          msg = "Will remain in the current safemode state."
    else:
      msg = "Must wait to leave safemode since High Availability is not enabled."
      check_for_safemode_off = True

    Logger.info(msg)

    # During a NonRolling (aka Express Upgrade), stay in safemode since the DataNodes are down.
    stay_in_safe_mode = False
    if upgrade_type == "nonrolling":
      stay_in_safe_mode = True

    if check_for_safemode_off:
      Logger.info("Stay in safe mode: {0}".format(stay_in_safe_mode))
      if not stay_in_safe_mode:
        Logger.info("Wait to leafe safemode since must transition from ON to OFF.")
        try:
          # Wait up to 30 mins
          Execute(is_namenode_safe_mode_off,
                  tries=65,
                  try_sleep=10,
                  user=params.hdfs_user,
                  logoutput=True
          )
        except Fail:
          Logger.error("NameNode is still in safemode, please be careful with commands that need safemode OFF.")

    # Always run this on non-HA, or active NameNode during HA.
    create_hdfs_directories(is_active_namenode_cmd)
    create_ranger_audit_hdfs_directories(is_active_namenode_cmd)

  elif action == "stop":
    import params
    service(
      action="stop", name="namenode", 
      user=params.hdfs_user
    )
  elif action == "status":
    import status_params
    check_process_status(status_params.namenode_pid_file)
  elif action == "decommission":
    decommission()

@OsFamilyFuncImpl(os_family=OSConst.WINSRV_FAMILY)
def namenode(action=None, hdfs_binary=None, do_format=True, upgrade_type=None, env=None):
  if action is None:
    raise Fail('"action" parameter is required for function namenode().')

  if action in ["start", "stop"] and hdfs_binary is None:
    raise Fail('"hdfs_binary" parameter is required for function namenode().')

  if action == "configure":
    pass
  elif action == "start":
    import params
    #TODO: Replace with format_namenode()
    namenode_format_marker = os.path.join(params.hadoop_conf_dir,"NN_FORMATTED")
    if not os.path.exists(namenode_format_marker):
      hadoop_cmd = "cmd /C %s" % (os.path.join(params.hadoop_home, "bin", "hadoop.cmd"))
      Execute("%s namenode -format" % (hadoop_cmd))
      open(namenode_format_marker, 'a').close()
    Service(params.namenode_win_service_name, action=action)
  elif action == "stop":
    import params
    Service(params.namenode_win_service_name, action=action)
  elif action == "status":
    import status_params
    check_windows_service_status(status_params.namenode_win_service_name)
  elif action == "decommission":
    decommission()

def create_name_dirs(directories):
  import params

  dirs = directories.split(",")
  Directory(dirs,
            mode=0755,
            owner=params.hdfs_user,
            group=params.user_group,
            create_parents = True,
            cd_access="a",
  )


def create_hdfs_directories(check):
  import params

  params.HdfsResource("/tmp",
                       type="directory",
                       action="create_on_execute",
                       owner=params.hdfs_user,
                       mode=0777,
                       only_if=check
  )
  params.HdfsResource(params.smoke_hdfs_user_dir,
                       type="directory",
                       action="create_on_execute",
                       owner=params.smoke_user,
                       mode=params.smoke_hdfs_user_mode,
                       only_if=check
  )
  params.HdfsResource(None, 
                      action="execute",
                      only_if=check #skip creation when HA not active
  )

def format_namenode(force=None):
  import params

  old_mark_dir = params.namenode_formatted_old_mark_dirs
  mark_dir = params.namenode_formatted_mark_dirs
  dfs_name_dir = params.dfs_name_dir
  hdfs_user = params.hdfs_user
  hadoop_conf_dir = params.hadoop_conf_dir

  if not params.dfs_ha_enabled:
    if force:
      ExecuteHadoop('namenode -format',
                    kinit_override=True,
                    bin_dir=params.hadoop_bin_dir,
                    conf_dir=hadoop_conf_dir)
    else:
      if not is_namenode_formatted(params):
        Execute(format("yes Y | hdfs --config {hadoop_conf_dir} namenode -format"),
                user = params.hdfs_user,
                path = [params.hadoop_bin_dir]
        )
        for m_dir in mark_dir:
          Directory(m_dir,
            create_parents = True
          )
  else:
    if params.dfs_ha_namenode_active is not None and \
       params.hostname == params.dfs_ha_namenode_active:
      # check and run the format command in the HA deployment scenario
      # only format the "active" namenode in an HA deployment
      if force:
        ExecuteHadoop('namenode -format',
                      kinit_override=True,
                      bin_dir=params.hadoop_bin_dir,
                      conf_dir=hadoop_conf_dir)
      else:
        if not is_namenode_formatted(params):
          Execute(format("yes Y | hdfs --config {hadoop_conf_dir} namenode -format"),
                  user = params.hdfs_user,
                  path = [params.hadoop_bin_dir]
          )
          for m_dir in mark_dir:
            Directory(m_dir,
              create_parents = True
            )

def is_namenode_formatted(params):
  old_mark_dirs = params.namenode_formatted_old_mark_dirs
  mark_dirs = params.namenode_formatted_mark_dirs
  nn_name_dirs = params.dfs_name_dir.split(',')
  marked = False
  # Check if name directories have been marked as formatted
  for mark_dir in mark_dirs:
    if os.path.isdir(mark_dir):
      marked = True
      print format("{mark_dir} exists. Namenode DFS already formatted")
    
  # Ensure that all mark dirs created for all name directories
  if marked:
    for mark_dir in mark_dirs:
      Directory(mark_dir,
        create_parents = True
      )      
    return marked  
  
  # Move all old format markers to new place
  for old_mark_dir in old_mark_dirs:
    if os.path.isdir(old_mark_dir):
      for mark_dir in mark_dirs:
        Execute(('cp', '-ar', old_mark_dir, mark_dir),
                sudo = True
        )
        marked = True
      Directory(old_mark_dir,
        action = "delete"
      )    
    elif os.path.isfile(old_mark_dir):
      for mark_dir in mark_dirs:
        Directory(mark_dir,
                  create_parents = True,
        )
      Directory(old_mark_dir,
        action = "delete"
      )
      marked = True
      
  # Check if name dirs are not empty
  for name_dir in nn_name_dirs:
    try:
      Execute(format("ls {name_dir} | wc -l  | grep -q ^0$"),
      )
      marked = False
    except Exception:
      marked = True
      print format("ERROR: Namenode directory(s) is non empty. Will not format the namenode. List of non-empty namenode dirs {nn_name_dirs}")
      break
       
  return marked

@OsFamilyFuncImpl(os_family=OsFamilyImpl.DEFAULT)
def decommission():
  import params

  hdfs_user = params.hdfs_user
  conf_dir = params.hadoop_conf_dir
  user_group = params.user_group
  nn_kinit_cmd = params.nn_kinit_cmd
  
  File(params.exclude_file_path,
       content=Template("exclude_hosts_list.j2"),
       owner=hdfs_user,
       group=user_group
  )
  
  if not params.update_exclude_file_only:
    Execute(nn_kinit_cmd,
            user=hdfs_user
    )

    if params.dfs_ha_enabled:
      # due to a bug in hdfs, refreshNodes will not run on both namenodes so we
      # need to execute each command scoped to a particular namenode
      nn_refresh_cmd = format('dfsadmin -fs hdfs://{namenode_rpc} -refreshNodes')
    else:
      nn_refresh_cmd = format('dfsadmin -fs {namenode_address} -refreshNodes')
    ExecuteHadoop(nn_refresh_cmd,
                  user=hdfs_user,
                  conf_dir=conf_dir,
                  kinit_override=True,
                  bin_dir=params.hadoop_bin_dir)

@OsFamilyFuncImpl(os_family=OSConst.WINSRV_FAMILY)
def decommission():
  import params
  hdfs_user = params.hdfs_user
  conf_dir = params.hadoop_conf_dir

  File(params.exclude_file_path,
       content=Template("exclude_hosts_list.j2"),
       owner=hdfs_user
  )

  if params.dfs_ha_enabled:
    # due to a bug in hdfs, refreshNodes will not run on both namenodes so we
    # need to execute each command scoped to a particular namenode
    nn_refresh_cmd = format('cmd /c hadoop dfsadmin -fs hdfs://{namenode_rpc} -refreshNodes')
  else:
    nn_refresh_cmd = format('cmd /c hadoop dfsadmin -fs {namenode_address} -refreshNodes')
  Execute(nn_refresh_cmd, user=hdfs_user)


def bootstrap_standby_namenode(params, use_path=False):

  bin_path = os.path.join(params.hadoop_bin_dir, '') if use_path else ""

  try:
    iterations = 50
    bootstrap_cmd = format("{bin_path}hdfs namenode -bootstrapStandby -nonInteractive")
    # Blue print based deployments start both NN in parallel and occasionally
    # the first attempt to bootstrap may fail. Depending on how it fails the
    # second attempt may not succeed (e.g. it may find the folder and decide that
    # bootstrap succeeded). The solution is to call with -force option but only
    # during initial start
    if params.command_phase == "INITIAL_START":
      bootstrap_cmd = format("{bin_path}hdfs namenode -bootstrapStandby -nonInteractive -force")
    Logger.info("Boostrapping standby namenode: %s" % (bootstrap_cmd))
    for i in range(iterations):
      Logger.info('Try %d out of %d' % (i+1, iterations))
      code, out = shell.call(bootstrap_cmd, logoutput=False, user=params.hdfs_user)
      if code == 0:
        Logger.info("Standby namenode bootstrapped successfully")
        return True
      elif code == 5:
        Logger.info("Standby namenode already bootstrapped")
        return True
      else:
        Logger.warning('Bootstrap standby namenode failed with %d error code. Will retry' % (code))
  except Exception as ex:
    Logger.error('Bootstrap standby namenode threw an exception. Reason %s' %(str(ex)))
  return False


def is_active_namenode(hdfs_binary):
  """
  Checks if current NameNode is active. Waits up to 30 seconds. If other NameNode is active returns False.
  :return: True if current NameNode is active, False otherwise
  """
  import params

  if params.dfs_ha_enabled:
    is_active_this_namenode_cmd = as_user(format("{hdfs_binary} --config {hadoop_conf_dir} haadmin -getServiceState {namenode_id} | grep active"), params.hdfs_user, env={'PATH':params.hadoop_bin_dir})
    is_active_other_namenode_cmd = as_user(format("{hdfs_binary} --config {hadoop_conf_dir} haadmin -getServiceState {other_namenode_id} | grep active"), params.hdfs_user, env={'PATH':params.hadoop_bin_dir})

    for i in range(0, 5):
      code, out = shell.call(is_active_this_namenode_cmd) # If active NN, code will be 0
      if code == 0: # active
        return True

      code, out = shell.call(is_active_other_namenode_cmd) # If other NN is active, code will be 0
      if code == 0: # other NN is active
        return False

      if i < 4: # Do not sleep after last iteration
        time.sleep(6)

    Logger.info("Active NameNode is not found.")
    return False

  else:
    return True
