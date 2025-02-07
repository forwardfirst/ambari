'''
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
'''

import socket
from unittest import TestCase
from mock.mock import patch, MagicMock

class TestHDP206StackAdvisor(TestCase):

  def setUp(self):
    import imp
    import os

    testDirectory = os.path.dirname(os.path.abspath(__file__))
    stackAdvisorPath = os.path.join(testDirectory, '../../../../../main/resources/stacks/stack_advisor.py')
    hdp206StackAdvisorPath = os.path.join(testDirectory, '../../../../../main/resources/stacks/HDP/2.0.6/services/stack_advisor.py')
    hdp206StackAdvisorClassName = 'HDP206StackAdvisor'
    with open(stackAdvisorPath, 'rb') as fp:
      stack_advisor = imp.load_module( 'stack_advisor', fp, stackAdvisorPath, ('.py', 'rb', imp.PY_SOURCE) )
    with open(hdp206StackAdvisorPath, 'rb') as fp:
      self.stack_advisor_impl = imp.load_module('stack_advisor_impl', fp, hdp206StackAdvisorPath, ('.py', 'rb', imp.PY_SOURCE))
    clazz = getattr(self.stack_advisor_impl, hdp206StackAdvisorClassName)
    self.stackAdvisor = clazz()
    self.maxDiff = None
    # substitute method in the instance
    self.get_system_min_uid_real = self.stackAdvisor.get_system_min_uid
    self.stackAdvisor.get_system_min_uid = self.get_system_min_uid_magic

  @patch('__builtin__.open')
  @patch('os.path.exists')
  def get_system_min_uid_magic(self, exists_mock, open_mock):
    class MagicFile(object):
      def read(self):
        return """
        #test line UID_MIN 200
        UID_MIN 500
        """

      def __exit__(self, exc_type, exc_val, exc_tb):
        pass

      def __enter__(self):
        return self

    exists_mock.return_value = True
    open_mock.return_value = MagicFile()
    return self.get_system_min_uid_real()



  def test_recommendationCardinalityALL(self):
    servicesInfo = [
      {
        "name": "GANGLIA",
        "components": [{"name": "GANGLIA_MONITOR", "cardinality": "ALL", "category": "SLAVE", "is_master": False}]
      }
    ]
    services = self.prepareServices(servicesInfo)
    hosts = self.prepareHosts(["host1", "host2"])
    result = self.stackAdvisor.recommendComponentLayout(services, hosts)

    expectedComponentsHostsMap = {
      "GANGLIA_MONITOR": ["host1", "host2"]
    }
    self.assertHostLayout(expectedComponentsHostsMap, result)

  def test_recommendationAssignmentNotChanged(self):
    servicesInfo = [
      {
        "name": "GANGLIA",
        "components": [{"name": "GANGLIA_MONITOR", "cardinality": "ALL", "category": "SLAVE", "is_master": False, "hostnames": ["host1"]}]
      }
    ]
    services = self.prepareServices(servicesInfo)
    hosts = self.prepareHosts(["host1", "host2"])
    result = self.stackAdvisor.recommendComponentLayout(services, hosts)

    expectedComponentsHostsMap = {
      "GANGLIA_MONITOR": ["host1", "host2"]
    }
    self.assertHostLayout(expectedComponentsHostsMap, result)

  def test_recommendationIsNotPreferableOnAmbariServer(self):
    servicesInfo = [
      {
        "name": "GANGLIA",
        "components": [{"name": "GANGLIA_SERVER", "cardinality": "ALL", "category": "MASTER", "is_master": True}]
      }
    ]
    services = self.prepareServices(servicesInfo)
    localhost = socket.getfqdn()
    hosts = self.prepareHosts([localhost, "host2"])
    result = self.stackAdvisor.recommendComponentLayout(services, hosts)

    expectedComponentsHostsMap = {
      "GANGLIA_SERVER": ["host2"]
    }
    self.assertHostLayout(expectedComponentsHostsMap, result)

  def test_validationNamenodeAndSecondaryNamenode2Hosts_noMessagesForSameHost(self):
    servicesInfo = [
      {
        "name": "HDFS",
        "components": [
          {"name": "NAMENODE", "cardinality": "1-2", "category": "MASTER", "is_master": True, "hostnames": ["host1"]},
          {"name": "SECONDARY_NAMENODE", "cardinality": "1", "category": "MASTER", "is_master": True, "hostnames": ["host1"]}]
      }
    ]
    services = self.prepareServices(servicesInfo)
    hosts = self.prepareHosts(["host1", "host2"])
    result = self.stackAdvisor.validateComponentLayout(services, hosts)

    expectedItems = [
      {"message": "Host is not used", "level": "ERROR", "host": "host2"}
    ]
    self.assertValidationResult(expectedItems, result)

  def test_validationCardinalityALL(self):
    servicesInfo = [
      {
        "name": "GANGLIA",
        "components": [
          {"name": "GANGLIA_MONITOR", "display_name": "Ganglia Monitor", "cardinality": "ALL", "category": "SLAVE", "is_master": False, "hostnames": ["host1"]},
          {"name": "GANGLIA_SERVER", "display_name": "Ganglia Server", "cardinality": "1-2", "category": "MASTER", "is_master": True, "hostnames": ["host2", "host1"]}
        ]
      }
    ]
    services = self.prepareServices(servicesInfo)
    hosts = self.prepareHosts(["host1", "host2"])
    result = self.stackAdvisor.validateComponentLayout(services, hosts)

    expectedItems = [
      {"message": "Ganglia Monitor component should be installed on all hosts in cluster.", "level": "ERROR"}
    ]
    self.assertValidationResult(expectedItems, result)

  def test_validationCardinalityExactAmount(self):
    servicesInfo = [
      {
        "name": "GANGLIA",
        "components": [
          {"name": "GANGLIA_MONITOR", "display_name": "Ganglia Monitor", "cardinality": "2", "category": "SLAVE", "is_master": False, "hostnames": ["host1"]},
          {"name": "GANGLIA_SERVER", "display_name": "Ganglia Server", "cardinality": "2", "category": "MASTER", "is_master": True, "hostnames": ["host2", "host1"]}
        ]
      }
    ]
    services = self.prepareServices(servicesInfo)
    hosts = self.prepareHosts(["host1", "host2"])
    result = self.stackAdvisor.validateComponentLayout(services, hosts)

    expectedItems = [
      {"message": "Exactly 2 Ganglia Monitor components should be installed in cluster.", "level": "ERROR"}
    ]
    self.assertValidationResult(expectedItems, result)

  def test_validationCardinalityAtLeast(self):
    servicesInfo = [
      {
        "name": "GANGLIA",
        "components": [
          {"name": "GANGLIA_MONITOR", "display_name": "Ganglia Monitor", "cardinality": "1+", "category": "SLAVE", "is_master": False, "hostnames": ["host1"]},
          {"name": "GANGLIA_SERVER", "display_name": "Ganglia Server", "cardinality": "3+", "category": "MASTER", "is_master": True, "hostnames": ["host2", "host1"]}
        ]
      }
    ]
    services = self.prepareServices(servicesInfo)
    hosts = self.prepareHosts(["host1", "host2"])
    result = self.stackAdvisor.validateComponentLayout(services, hosts)

    expectedItems = [
      {"message": "At least 3 Ganglia Server components should be installed in cluster.", "level": "ERROR"}
    ]
    self.assertValidationResult(expectedItems, result)

  def test_validationWarnMessagesIfLessThanDefault(self):
    servicesInfo = [
      {
        "name": "YARN",
        "components": []
      }
    ]
    services = self.prepareServices(servicesInfo)
    services["configurations"] = {"yarn-site":{"properties":{"yarn.nodemanager.resource.memory-mb": "0",
                                                             "yarn.scheduler.minimum-allocation-mb": "str"}}}
    hosts = self.prepareHosts([])
    result = self.stackAdvisor.validateConfigurations(services, hosts)

    expectedItems = [
      {"message": "Value is less than the recommended default of 512", "level": "WARN"},
      {'message': 'Value should be set for yarn.nodemanager.linux-container-executor.group', 'level': 'ERROR'},
      {"message": "Value should be integer", "level": "ERROR"},
      {"message": "Value should be set", "level": "ERROR"}
    ]
    self.assertValidationResult(expectedItems, result)

  def test_validationMinMax(self):

    configurations = {
      "mapred-site": {
        "properties": {
          "mapreduce.task.io.sort.mb": "4096",
          "some_float_value": "0.5",
          "no_min_or_max_attribute_property": "STRING_VALUE"
        }
      }
    }
    recommendedDefaults = {
      "mapred-site": {
        "properties": {
          "mapreduce.task.io.sort.mb": "2047",
          "some_float_value": "0.8",
          "no_min_or_max_attribute_property": "STRING_VALUE"
        },
        "property_attributes": {
          'mapreduce.task.io.sort.mb': {'maximum': '2047'},
          'some_float_value': {'minimum': '0.8'}
        }
      }
    }
    items = []
    self.stackAdvisor.validateMinMax(items, recommendedDefaults, configurations)

    expectedItems = [
      {
        'message': 'Value is greater than the recommended maximum of 2047 ',
        'level': 'WARN',
        'config-type':  'mapred-site',
        'config-name': 'mapreduce.task.io.sort.mb',
        'type': 'configuration'
      },
      {
        'message': 'Value is less than the recommended minimum of 0.8 ',
        'level': 'WARN',
        'config-type':  'mapred-site',
        'config-name': 'some_float_value',
        'type': 'configuration'
      }
    ]
    self.assertEquals(expectedItems, items)

  def test_validationHostIsNotUsedForNonValuableComponent(self):
    servicesInfo = [
      {
        "name": "GANGLIA",
        "components": [
          {"name": "GANGLIA_MONITOR", "cardinality": "ALL", "category": "SLAVE", "is_master": False, "hostnames": ["host1", "host2"]},
          {"name": "GANGLIA_SERVER", "cardinality": "1", "category": "MASTER", "is_master": True, "hostnames": ["host2"]}
        ]
      }
    ]
    services = self.prepareServices(servicesInfo)
    hosts = self.prepareHosts(["host1", "host2"])
    result = self.stackAdvisor.validateComponentLayout(services, hosts)

    expectedItems = [
      {"message": "Host is not used", "host": "host1", "level": "ERROR"}
    ]
    self.assertValidationResult(expectedItems, result)

  def test_validationCardinality01TwoHostsAssigned(self):
    servicesInfo = [
      {
        "name": "GANGLIA",
        "components": [
          {"name": "GANGLIA_SERVER", "display_name": "Ganglia Server", "cardinality": "0-1", "category": "MASTER", "is_master": True, "hostnames": ["host1", "host2"]}
        ]
      }
    ]
    services = self.prepareServices(servicesInfo)
    hosts = self.prepareHosts(["host1", "host2"])
    result = self.stackAdvisor.validateComponentLayout(services, hosts)

    expectedItems = [
      {"message": "Between 0 and 1 Ganglia Server components should be installed in cluster.", "level": "ERROR"}
    ]
    self.assertValidationResult(expectedItems, result)

  def test_validationHostIsNotUsed(self):
    servicesInfo = [
      {
        "name": "GANGLIA",
        "components": [
          {"name": "GANGLIA_SERVER", "cardinality": "1", "category": "MASTER", "is_master": True, "hostnames": ["host1"]}
        ]
      }
    ]
    services = self.prepareServices(servicesInfo)
    hosts = self.prepareHosts(["host1", "host2"])
    result = self.stackAdvisor.validateComponentLayout(services, hosts)

    expectedItems = [
      {"message": "Host is not used", "host": "host2", "level": "ERROR"}
    ]
    self.assertValidationResult(expectedItems, result)

  def test_getConfigurationClusterSummary_withHBaseAnd6gbRam(self):
    servicesList = ["HBASE"]
    components = []
    hosts = {
      "items" : [
        {
          "Hosts" : {
            "cpu_count" : 8,
            "total_mem" : 6291456,
            "disk_info" : [
              {"mountpoint" : "/"},
              {"mountpoint" : "/dev/shm"},
              {"mountpoint" : "/vagrant"},
              {"mountpoint" : "/"},
              {"mountpoint" : "/dev/shm"},
              {"mountpoint" : "/"},
              {"mountpoint" : "/dev/shm"},
              {"mountpoint" : "/vagrant"}
            ]
          }
        }
      ]
    }
    expected = {
      "hBaseInstalled": True,
      "components": components,
      "cpu": 8,
      "disk": 8,
      "ram": 6,
      "reservedRam": 2,
      "hbaseRam": 1,
      "minContainerSize": 512,
      "totalAvailableRam": 3072,
      "containers": 6,
      "ramPerContainer": 512,
      "mapMemory": 512,
      "reduceMemory": 512,
      "amMemory": 512,
      "referenceHost": hosts["items"][0]["Hosts"]
    }

    # Test - Cluster data with 1 host
    result = self.stackAdvisor.getConfigurationClusterSummary(servicesList, hosts, components, None)
    self.assertEquals(result, expected)

    # Test - Cluster data with 2 hosts - pick minimum memory
    servicesList.append("YARN")
    services = services = {"services":
                  [{"StackServices":
                      {"service_name" : "YARN",
                       "service_version" : "2.6.0.2.2"
                      },
                    "components":[
                      {
                        "StackServiceComponents":{
                          "advertise_version":"true",
                          "cardinality":"1+",
                          "component_category":"SLAVE",
                          "component_name":"NODEMANAGER",
                          "custom_commands":[

                          ],
                          "display_name":"NodeManager",
                          "is_client":"false",
                          "is_master":"false",
                          "service_name":"YARN",
                          "stack_name":"HDP",
                          "stack_version":"2.2",
                          "hostnames":[
                            "host1",
                            "host2"
                          ]
                        },
                        "dependencies":[
                        ]
                      }
                      ],
                    }],
                "configurations": {}
    }
    hosts["items"][0]["Hosts"]["host_name"] = "host1"
    hosts["items"].append({
        "Hosts": {
            "cpu_count" : 4,
            "total_mem" : 500000,
            "host_name" : "host2",
            "disk_info" : [
              {"mountpoint" : "/"},
              {"mountpoint" : "/dev/shm"},
              {"mountpoint" : "/vagrant"},
              {"mountpoint" : "/"},
              {"mountpoint" : "/dev/shm"},
              {"mountpoint" : "/"},
              {"mountpoint" : "/dev/shm"},
              {"mountpoint" : "/vagrant"}
            ]
          }
        })
    expected["referenceHost"] = hosts["items"][1]["Hosts"]
    expected["referenceNodeManagerHost"] = hosts["items"][1]["Hosts"]
    expected["amMemory"] = 170.66666666666666
    expected["containers"] = 3.0
    expected["cpu"] = 4
    expected["totalAvailableRam"] = 512
    expected["mapMemory"] = 170
    expected["minContainerSize"] = 256
    expected["reduceMemory"] = 170.66666666666666
    expected["ram"] = 0
    expected["ramPerContainer"] = 170.66666666666666
    expected["reservedRam"] = 1
    result = self.stackAdvisor.getConfigurationClusterSummary(servicesList, hosts, components, services)
    self.assertEquals(result, expected)


  def test_getConfigurationClusterSummary_withHBaseAnd48gbRam(self):
    servicesList = ["HBASE"]
    components = []
    hosts = {
      "items" : [
        {
          "Hosts" : {
            "cpu_count" : 6,
            "total_mem" : 50331648,
            "disk_info" : [
              {"mountpoint" : "/"},
              {"mountpoint" : "/dev/shm"},
              {"mountpoint" : "/vagrant"},
              {"mountpoint" : "/"},
              {"mountpoint" : "/dev/shm"},
              {"mountpoint" : "/vagrant"}
            ]
          }
        }
      ]
    }
    expected = {
      "hBaseInstalled": True,
      "components": components,
      "cpu": 6,
      "disk": 6,
      "ram": 48,
      "reservedRam": 6,
      "hbaseRam": 8,
      "minContainerSize": 2048,
      "totalAvailableRam": 34816,
      "containers": 11,
      "ramPerContainer": 3072,
      "mapMemory": 3072,
      "reduceMemory": 3072,
      "amMemory": 3072,
      "referenceHost": hosts["items"][0]["Hosts"]
    }

    result = self.stackAdvisor.getConfigurationClusterSummary(servicesList, hosts, components, None)

    self.assertEquals(result, expected)

  def test_recommendStormConfigurations(self):
    # no AMS
    configurations = {}
    services = {
      "services":  [
      ],
      "configurations": configurations
    }

    expected = {
      "storm-site": {
        "properties": {
        }
      },
    }

    self.stackAdvisor.recommendStormConfigurations(configurations, None, services, None)
    self.assertEquals(configurations, expected)

    # with AMS
    configurations = {}
    services = {
      "services":  [
        {
          "StackServices": {
            "service_name": "AMBARI_METRICS"
          }
        }
      ],
      "configurations": configurations
    }

    expected = {
      "storm-site": {
        "properties": {
          "metrics.reporter.register": "org.apache.hadoop.metrics2.sink.storm.StormTimelineMetricsReporter"
        }
      },
    }

    self.stackAdvisor.recommendStormConfigurations(configurations, None, services, None)
    self.assertEquals(configurations, expected)

  def test_recommendYARNConfigurations(self):
    configurations = {}
    services = {"configurations": configurations}
    clusterData = {
      "containers" : 5,
      "ramPerContainer": 256
    }
    expected = {
      "yarn-env": {
        "properties": {
          "min_user_id": "500"
        }
      },
      "yarn-site": {
        "properties": {
          "yarn.nodemanager.linux-container-executor.group": "hadoop",
          "yarn.nodemanager.resource.memory-mb": "1280",
          "yarn.scheduler.minimum-allocation-mb": "256",
          "yarn.scheduler.maximum-allocation-mb": "1280"
        }
      }
    }

    self.stackAdvisor.recommendYARNConfigurations(configurations, clusterData, services, None)
    self.assertEquals(configurations, expected)

  def test_recommendMapReduce2Configurations_mapMemoryLessThan2560(self):
    configurations = {}
    clusterData = {
      "mapMemory": 567,
      "reduceMemory": 345.6666666666666,
      "amMemory": 123.54
    }
    expected = {
      "mapred-site": {
        "properties": {
          "yarn.app.mapreduce.am.resource.mb": "123",
          "yarn.app.mapreduce.am.command-opts": "-Xmx99m",
          "mapreduce.map.memory.mb": "567",
          "mapreduce.reduce.memory.mb": "345",
          "mapreduce.map.java.opts": "-Xmx454m",
          "mapreduce.reduce.java.opts": "-Xmx277m",
          "mapreduce.task.io.sort.mb": "227"
        }
      }
    }

    self.stackAdvisor.recommendMapReduce2Configurations(configurations, clusterData, None, None)
    self.assertEquals(configurations, expected)

  def test_getConfigurationClusterSummary_noHostsWithoutHBase(self):
    servicesList = []
    components = []
    hosts = {
      "items" : []
    }
    result = self.stackAdvisor.getConfigurationClusterSummary(servicesList, hosts, components, None)

    expected = {
      "hBaseInstalled": False,
      "components": components,
      "cpu": 0,
      "disk": 0,
      "ram": 0,
      "reservedRam": 1,
      "hbaseRam": 1,
      "minContainerSize": 256,
      "totalAvailableRam": 512,
      "containers": 3,
      "ramPerContainer": 170.66666666666666,
      "mapMemory": 170,
      "reduceMemory": 170.66666666666666,
      "amMemory": 170.66666666666666
    }

    self.assertEquals(result, expected)

  def prepareHosts(self, hostsNames):
    hosts = { "items": [] }
    for hostName in hostsNames:
      nextHost = {"Hosts":{"host_name" : hostName}}
      hosts["items"].append(nextHost)
    return hosts

  def prepareServices(self, servicesInfo):
    services = { "Versions" : { "stack_name" : "HDP", "stack_version" : "2.0.6" } }
    services["services"] = []

    for serviceInfo in servicesInfo:
      nextService = {"StackServices":{"service_name" : serviceInfo["name"]}}
      nextService["components"] = []
      for component in serviceInfo["components"]:
        nextComponent = {
          "StackServiceComponents": {
            "component_name": component["name"],
            "cardinality": component["cardinality"],
            "component_category": component["category"],
            "is_master": component["is_master"]
          }
        }
        try:
          nextComponent["StackServiceComponents"]["hostnames"] = component["hostnames"]
        except KeyError:
          nextComponent["StackServiceComponents"]["hostnames"] = []
        try:
          nextComponent["StackServiceComponents"]["display_name"] = component["display_name"]
        except KeyError:
          nextComponent["StackServiceComponents"]["display_name"] = component["name"]
        nextService["components"].append(nextComponent)
      services["services"].append(nextService)

    return services

  def assertHostLayout(self, componentsHostsMap, recommendation):
    blueprintMapping = recommendation["recommendations"]["blueprint"]["host_groups"]
    bindings = recommendation["recommendations"]["blueprint_cluster_binding"]["host_groups"]

    actualComponentHostsMap = {}
    for hostGroup in blueprintMapping:
      hostGroupName = hostGroup["name"]
      hostsInfos = [binding["hosts"] for binding in bindings if binding["name"] == hostGroupName][0]
      hosts = [info["fqdn"] for info in hostsInfos]

      for component in hostGroup["components"]:
        componentName = component["name"]
        try:
          actualComponentHostsMap[componentName]
        except KeyError, err:
          actualComponentHostsMap[componentName] = []
        for host in hosts:
          if host not in actualComponentHostsMap[componentName]:
            actualComponentHostsMap[componentName].append(host)

    for componentName in componentsHostsMap.keys():
      expectedHosts = componentsHostsMap[componentName]
      actualHosts = actualComponentHostsMap[componentName]
      self.checkEqual(expectedHosts, actualHosts)

  def checkEqual(self, l1, l2):
    if not len(l1) == len(l2) or not sorted(l1) == sorted(l2):
      raise AssertionError("list1={0}, list2={1}".format(l1, l2))

  def assertValidationResult(self, expectedItems, result):
    actualItems = []
    for item in result["items"]:
      next = {"message": item["message"], "level": item["level"]}
      try:
        next["host"] = item["host"]
      except KeyError, err:
        pass
      actualItems.append(next)
    self.checkEqual(expectedItems, actualItems)

  def test_recommendHbaseConfigurations(self):
    servicesList = ["HBASE"]
    configurations = {}
    components = []
    hosts = {
      "items" : [
        {
          "Hosts" : {
            "cpu_count" : 6,
            "total_mem" : 50331648,
            "disk_info" : [
              {"mountpoint" : "/"},
              {"mountpoint" : "/dev/shm"},
              {"mountpoint" : "/vagrant"},
              {"mountpoint" : "/"},
              {"mountpoint" : "/dev/shm"},
              {"mountpoint" : "/vagrant"}
            ]
          }
        }
      ]
    }
    services = {
      "services" : [
      ],
      "configurations": {
        "hbase-site": {
          "properties": {
            "hbase.superuser": "hbase"
          }
        },
        "hbase-env": {
          "properties": {
            "hbase_user": "hbase123"
          }
        }
      }
    }
    expected = {
      'hbase-site': {
        'properties': {
          'hbase.superuser': 'hbase123'
        }
      },
      "hbase-env": {
        "properties": {
          "hbase_master_heapsize": "8192",
          "hbase_regionserver_heapsize": "8192",
          }
      }
    }

    clusterData = self.stackAdvisor.getConfigurationClusterSummary(servicesList, hosts, components, None)
    self.assertEquals(clusterData['hbaseRam'], 8)

    self.stackAdvisor.recommendHbaseConfigurations(configurations, clusterData, services, None)
    self.assertEquals(configurations, expected)


  def test_recommendRangerConfigurations(self):
    clusterData = {}
    # Recommend for not existing DB_FLAVOR and http enabled, HDP-2.3
    services = {
      "Versions" : {
        "stack_version" : "2.3",
      },
      "services":  [
        {
          "StackServices": {
            "service_name": "RANGER",
            "service_version": "0.5.0"
          },
          "components": [
            {
              "StackServiceComponents": {
                "component_name": "RANGER_ADMIN",
                "hostnames": ["host1"]
              }
            }
          ]
        },
        {
          "StackServices": {
            "service_name": "HDFS"
          },
          "components": [
            {
              "StackServiceComponents": {
                "component_name": "NAMENODE",
                "hostnames": ["host1"]
              }
            }
          ]
        }
      ],
      "configurations": {
        "admin-properties": {
          "properties": {
            "DB_FLAVOR": "NOT_EXISTING",
            }
        },
        "ranger-admin-site": {
          "properties": {
            "ranger.service.http.port": "7777",
            "ranger.service.http.enabled": "true",
            }
        }
      }
    }
    expected = {
      "admin-properties": {
        "properties": {
          "SQL_CONNECTOR_JAR": "/usr/share/java/mysql-connector-java.jar",
          "policymgr_external_url": "http://host1:7777",
        }
      }
    }
    recommendedConfigurations = {}
    self.stackAdvisor.recommendRangerConfigurations(recommendedConfigurations, clusterData, services, None)
    self.assertEquals(recommendedConfigurations, expected, "Test for not existing DB_FLAVOR and http enabled, HDP-2.3")

    # Recommend for DB_FLAVOR POSTGRES and https enabled, HDP-2.3
    configurations = {
      "admin-properties": {
        "properties": {
          "DB_FLAVOR": "POSTGRES",
          }
      },
      "ranger-admin-site": {
        "properties": {
          "ranger.service.https.port": "7777",
          "ranger.service.http.enabled": "false",
          }
      }
    }
    services['configurations'] = configurations

    expected = {
      "admin-properties": {
        "properties": {
          "SQL_CONNECTOR_JAR": "/usr/share/java/postgresql.jar",
          "policymgr_external_url": "https://host1:7777",
          }
      }
    }
    recommendedConfigurations = {}
    self.stackAdvisor.recommendRangerConfigurations(recommendedConfigurations, clusterData, services, None)
    self.assertEquals(recommendedConfigurations, expected, "Test for DB_FLAVOR POSTGRES and https enabled, HDP-2.3")

    # Recommend for DB_FLAVOR ORACLE and https enabled, HDP-2.2
    configurations = {
      "admin-properties": {
        "properties": {
          "DB_FLAVOR": "ORACLE",
          }
      },
      "ranger-site": {
        "properties": {
          "http.enabled": "false",
          "https.service.port": "8888",
          }
      }
    }
    services['configurations'] = configurations
    expected = {
      "admin-properties": {
        "properties": {
          "SQL_CONNECTOR_JAR": "/usr/share/java/ojdbc6.jar",
          "policymgr_external_url": "https://host1:8888",
          }
      },
      "ranger-env": {"properties": {}}
    }

    recommendedConfigurations = {}
    services['services'][0]['StackServices']['service_version'] = "0.4.0"
    self.stackAdvisor.recommendRangerConfigurations(recommendedConfigurations, clusterData, services, None)
    self.assertEquals(recommendedConfigurations, expected, "Test for DB_FLAVOR ORACLE and https enabled, HDP-2.2")

    # Test Recommend LDAP values
    services["ambari-server-properties"] = {
      "ambari.ldap.isConfigured" : "true",
      "authentication.ldap.bindAnonymously" : "false",
      "authentication.ldap.baseDn" : "dc=apache,dc=org",
      "authentication.ldap.groupNamingAttr" : "cn",
      "authentication.ldap.primaryUrl" : "c6403.ambari.apache.org:636",
      "authentication.ldap.userObjectClass" : "posixAccount",
      "authentication.ldap.secondaryUrl" : "c6403.ambari.apache.org:636",
      "authentication.ldap.usernameAttribute" : "uid",
      "authentication.ldap.dnAttribute" : "dn",
      "authentication.ldap.useSSL" : "true",
      "authentication.ldap.managerPassword" : "/etc/ambari-server/conf/ldap-password.dat",
      "authentication.ldap.groupMembershipAttr" : "memberUid",
      "authentication.ldap.groupObjectClass" : "posixGroup",
      "authentication.ldap.managerDn" : "uid=hdfs,ou=people,ou=dev,dc=apache,dc=org"
    }
    services["configurations"] = {}
    expected = {
      'admin-properties': {
        'properties': {
          'policymgr_external_url': 'http://host1:6080',
        }
      },
      'ranger-env': {'properties': {}},
      'usersync-properties': {
        'properties': {
          'SYNC_LDAP_URL': 'ldaps://c6403.ambari.apache.org:636',
          'SYNC_LDAP_BIND_DN': 'uid=hdfs,ou=people,ou=dev,dc=apache,dc=org',
          'SYNC_LDAP_USER_OBJECT_CLASS': 'posixAccount',
          'SYNC_LDAP_USER_NAME_ATTRIBUTE': 'uid'
        }
      }
    }
    recommendedConfigurations = {}
    self.stackAdvisor.recommendRangerConfigurations(recommendedConfigurations, clusterData, services, None)
    self.assertEquals(recommendedConfigurations, expected, "Test Recommend LDAP values")

    # Test Ranger Audit properties
    del services["ambari-server-properties"]
    services["configurations"] = {
      "core-site": {
        "properties": {
          "fs.defaultFS": "hdfs://host1:8080",
        }
      },
      "ranger-env": {
        "properties": {
          "xasecure.audit.destination.db": "true",
          "xasecure.audit.destination.hdfs":"false",
          "xasecure.audit.destination.hdfs.dir":"hdfs://localhost:8020/ranger/audit/%app-type%/%time:yyyyMMdd%"
        }
      },
      "ranger-hdfs-plugin-properties": {
        "properties": {}
      }
    }
    expected = {
      'admin-properties': {
        'properties': {
          'policymgr_external_url': 'http://host1:6080'
        }
      },
      'ranger-hdfs-plugin-properties': {
        'properties': {
          'XAAUDIT.HDFS.IS_ENABLED': 'false',
          'XAAUDIT.HDFS.DESTINATION_DIRECTORY': 'hdfs://host1:8080/ranger/audit/%app-type%/%time:yyyyMMdd%',
          'XAAUDIT.DB.IS_ENABLED': 'true'
        }
      },
      'ranger-env': {
        'properties': {
          'xasecure.audit.destination.hdfs.dir': 'hdfs://host1:8080/ranger/audit/%app-type%/%time:yyyyMMdd%'
        }
      }
    }

    recommendedConfigurations = {}
    self.stackAdvisor.recommendRangerConfigurations(recommendedConfigurations, clusterData, services, None)
    self.assertEquals(recommendedConfigurations, expected, "Test Ranger Audit properties")



  def test_recommendHDFSConfigurations(self):
    configurations = {
      "hadoop-env": {
        "properties": {
          "hdfs_user": "hdfs",
          "proxyuser_group": "users"
        }
      },
      "hive-env": {
        "properties": {
          "webhcat_user": "webhcat",
          "hive_user": "hive"
        }
      },
      "oozie-env": {
        "properties": {
          "oozie_user": "oozie"
        }
      },
      "falcon-env": {
        "properties": {
          "falcon_user": "falcon"
        }
      }
    }

    hosts = {
      "items": [
        {
          "href": "/api/v1/hosts/host1",
          "Hosts": {
            "cpu_count": 1,
            "host_name": "c6401.ambari.apache.org",
            "os_arch": "x86_64",
            "os_type": "centos6",
            "ph_cpu_count": 1,
            "public_host_name": "c6401.ambari.apache.org",
            "rack_info": "/default-rack",
            "total_mem": 2097152
          }
        }]}

    services = {
      "services": [
        {
          "StackServices": {
            "service_name": "HDFS"
          }, "components": []
        },
        {
          "StackServices": {
            "service_name": "FALCON"
          }, "components": []
        },
        {
          "StackServices": {
            "service_name": "HIVE"
          }, "components": [{
          "href": "/api/v1/stacks/HDP/versions/2.0.6/services/HIVE/components/HIVE_SERVER",
          "StackServiceComponents": {
            "advertise_version": "true",
            "cardinality": "1",
            "component_category": "MASTER",
            "component_name": "HIVE_SERVER",
            "custom_commands": [],
            "display_name": "Hive Server",
            "is_client": "false",
            "is_master": "true",
            "service_name": "HIVE",
            "stack_name": "HDP",
            "stack_version": "2.0.6",
            "hostnames": ["c6401.ambari.apache.org"]
          }, }]
        },
        {
          "StackServices": {
            "service_name": "OOZIE"
          }, "components": [{
          "href": "/api/v1/stacks/HDP/versions/2.0.6/services/HIVE/components/OOZIE_SERVER",
          "StackServiceComponents": {
            "advertise_version": "true",
            "cardinality": "1",
            "component_category": "MASTER",
            "component_name": "OOZIE_SERVER",
            "custom_commands": [],
            "display_name": "Oozie Server",
            "is_client": "false",
            "is_master": "true",
            "service_name": "HIVE",
            "stack_name": "HDP",
            "stack_version": "2.0.6",
            "hostnames": ["c6401.ambari.apache.org"]
          }, }]
        }],
      "configurations": configurations
    }

    clusterData = {
      "totalAvailableRam": 2048
    }
    expected = {'oozie-env':
                  {'properties':
                     {'oozie_user': 'oozie'}},
                'core-site':
                  {'properties':
                     {'hadoop.proxyuser.oozie.groups': '*',
                      'hadoop.proxyuser.hive.groups': '*',
                      'hadoop.proxyuser.webhcat.hosts': 'c6401.ambari.apache.org',
                      'hadoop.proxyuser.falcon.hosts': '*',
                      'hadoop.proxyuser.webhcat.groups': '*',
                      'hadoop.proxyuser.hdfs.groups': '*',
                      'hadoop.proxyuser.hdfs.hosts': '*',
                      'hadoop.proxyuser.hive.hosts': 'c6401.ambari.apache.org',
                      'hadoop.proxyuser.oozie.hosts': 'c6401.ambari.apache.org',
                      'hadoop.proxyuser.falcon.groups': '*'}},
                'falcon-env':
                  {'properties':
                     {'falcon_user': 'falcon'}},
                'hive-env':
                  {'properties':
                     {'hive_user': 'hive',
                      'webhcat_user': 'webhcat'}},
                'hdfs-site':
                  {'properties': {}},
                'hadoop-env':
                  {'properties':
                     {'hdfs_user': 'hdfs',
                      'namenode_heapsize': '1024',
                      'proxyuser_group': 'users',
                      'namenode_opt_maxnewsize': '256',
                      'namenode_opt_newsize': '256'}}}

    self.stackAdvisor.recommendHDFSConfigurations(configurations, clusterData, services, hosts)
    self.assertEquals(configurations, expected)

    configurations["hadoop-env"]["properties"]['hdfs_user'] = "hdfs1"

    changedConfigurations = [{"type":"hadoop-env",
                              "name":"hdfs_user",
                              "old_value":"hdfs"}]

    services["changed-configurations"] = changedConfigurations
    services['configurations'] = configurations

    expected = {'oozie-env':
                  {'properties':
                     {'oozie_user': 'oozie'}},
                'core-site': {'properties':
                                {'hadoop.proxyuser.oozie.groups': '*',
                                 'hadoop.proxyuser.hive.groups': '*',
                                 'hadoop.proxyuser.hdfs1.groups': '*',
                                 'hadoop.proxyuser.hdfs1.hosts': '*',
                                 'hadoop.proxyuser.webhcat.hosts': 'c6401.ambari.apache.org',
                                 'hadoop.proxyuser.falcon.hosts': '*',
                                 'hadoop.proxyuser.webhcat.groups': '*',
                                 'hadoop.proxyuser.hdfs.groups': '*',
                                 'hadoop.proxyuser.hdfs.hosts': '*',
                                 'hadoop.proxyuser.hive.hosts': 'c6401.ambari.apache.org',
                                 'hadoop.proxyuser.oozie.hosts': 'c6401.ambari.apache.org',
                                 'hadoop.proxyuser.falcon.groups': '*'},
                              'property_attributes':
                                {'hadoop.proxyuser.hdfs.groups': {'delete': 'true'},
                                 'hadoop.proxyuser.hdfs.hosts': {'delete': 'true'}}},
                'falcon-env':
                  {'properties':
                     {'falcon_user': 'falcon'}},
                'hive-env':
                  {'properties':
                     {'hive_user': 'hive',
                      'webhcat_user': 'webhcat'}},
                'hdfs-site':
                  {'properties': {}},
                'hadoop-env':
                  {'properties':
                     {'hdfs_user': 'hdfs1',
                      'namenode_heapsize': '1024',
                      'proxyuser_group': 'users',
                      'namenode_opt_maxnewsize': '256',
                      'namenode_opt_newsize': '256'}}}

    self.stackAdvisor.recommendHDFSConfigurations(configurations, clusterData, services, hosts)
    self.assertEquals(configurations, expected)

    # Verify dfs.namenode.rpc-address is recommended to be deleted when NN HA
    configurations["hdfs-site"]["properties"]['dfs.nameservices'] = "mycluster"
    configurations["hdfs-site"]["properties"]['dfs.ha.namenodes.mycluster'] = "nn1,nn2"
    services['configurations'] = configurations
    expected["hdfs-site"] = {
      'properties': {
        'dfs.nameservices': 'mycluster',
        'dfs.ha.namenodes.mycluster': 'nn1,nn2'
      },
      'property_attributes': {
        'dfs.namenode.rpc-address': {
          'delete': 'true'
        }
      }
    }
    self.stackAdvisor.recommendHDFSConfigurations(configurations, clusterData, services, hosts)
    self.assertEquals(configurations, expected)


  def test_getHostNamesWithComponent(self):

    services = {
      "services":  [
        {
          "StackServices": {
            "service_name": "SERVICE"
          },
          "components": [
            {
              "StackServiceComponents": {
                "component_name": "COMPONENT",
                "hostnames": ["host1","host2","host3"]
              }
            }
          ]
        }
      ],
      "configurations": {}
    }

    result = self.stackAdvisor.getHostNamesWithComponent("SERVICE","COMPONENT", services)
    expected = ["host1","host2","host3"]
    self.assertEquals(result, expected)


  def test_getZKHostPortString(self):
    configurations = {
      "zoo.cfg": {
        "properties": {
          'clientPort': "2183"
        }
      }
    }

    services = {
      "services":  [
        {
          "StackServices": {
            "service_name": "ZOOKEEPER"
          },
          "components": [
            {
              "StackServiceComponents": {
                "component_name": "ZOOKEEPER_SERVER",
                "hostnames": ["zk.host1","zk.host2","zk.host3"]
              }
            }, {
              "StackServiceComponents": {
                "component_name": "ZOOKEEPER_CLIENT",
                "hostnames": ["host1"]
              }
            }
          ]
        }
      ],
      "configurations": configurations
    }

    result = self.stackAdvisor.getZKHostPortString(services)
    expected = "zk.host1:2183,zk.host2:2183,zk.host3:2183"
    self.assertEquals(result, expected)

  def test_validateHDFSConfigurationsEnv(self):
    configurations = {}

    # 1) ok: namenode_heapsize > recommended
    recommendedDefaults = {'namenode_heapsize': '1024',
                           'namenode_opt_newsize' : '256',
                           'namenode_opt_maxnewsize' : '256'}
    properties = {'namenode_heapsize': '2048',
                  'namenode_opt_newsize' : '300',
                  'namenode_opt_maxnewsize' : '300'}
    res_expected = []

    res = self.stackAdvisor.validateHDFSConfigurationsEnv(properties, recommendedDefaults, configurations, '', '')
    self.assertEquals(res, res_expected)

    # 2) fail: namenode_heapsize, namenode_opt_maxnewsize < recommended
    properties['namenode_heapsize'] = '1022'
    properties['namenode_opt_maxnewsize'] = '255'
    res_expected = [{'config-type': 'hadoop-env',
                     'message': 'Value is less than the recommended default of 1024',
                     'type': 'configuration',
                     'config-name': 'namenode_heapsize',
                     'level': 'WARN'},
                    {'config-name': 'namenode_opt_maxnewsize',
                     'config-type': 'hadoop-env',
                     'level': 'WARN',
                     'message': 'Value is less than the recommended default of 256',
                     'type': 'configuration'}]

    res = self.stackAdvisor.validateHDFSConfigurationsEnv(properties, recommendedDefaults, configurations, '', '')
    self.assertEquals(res, res_expected)

  def test_validateAmsHbaseSiteConfigurations(self):
    configurations = {
      "hdfs-site": {
        "properties": {
          'dfs.datanode.data.dir': "/hadoop/data"
        }
      },
      "core-site": {
        "properties": {
          "fs.defaultFS": "hdfs://c6401.ambari.apache.org:8020"
        }
      },
      "ams-site": {
        "properties": {
          "timeline.metrics.service.operation.mode": "embedded"
        }
      }
    }

    recommendedDefaults = {
      'hbase.rootdir': 'file:///var/lib/ambari-metrics-collector/hbase',
      'hbase.tmp.dir': '/var/lib/ambari-metrics-collector/hbase',
      'hbase.cluster.distributed': 'false'
    }
    properties = {
      'hbase.rootdir': 'file:///var/lib/ambari-metrics-collector/hbase',
      'hbase.tmp.dir' : '/var/lib/ambari-metrics-collector/hbase',
      'hbase.cluster.distributed': 'false'
    }
    host = {
      "href" : "/api/v1/hosts/host1",
      "Hosts" : {
        "cpu_count" : 1,
        "host_name" : "host1",
        "os_arch" : "x86_64",
        "os_type" : "centos6",
        "ph_cpu_count" : 1,
        "public_host_name" : "host1",
        "rack_info" : "/default-rack",
        "total_mem" : 2097152,
        "disk_info": [
          {
            "available": str(15<<30), # 15 GB
            "type": "ext4",
            "mountpoint": "/"
          }
        ]
      }
    }

    hosts = {
      "items" : [
        host
      ]
    }

    services = {
      "services":  [
        {
          "StackServices": {
            "service_name": "AMBARI_METRICS"
          },
          "components": [
            {
              "StackServiceComponents": {
                "component_name": "METRICS_COLLECTOR",
                "hostnames": ["host1"]
              }
            }, {
              "StackServiceComponents": {
                "component_name": "METRICS_MONITOR",
                "hostnames": ["host1"]
              }
            }
          ]
        },
        {
          "StackServices": {
            "service_name": "HDFS"
          },
          "components": [
            {
              "StackServiceComponents": {
                "component_name": "DATANODE",
                "hostnames": ["host1"]
              }
            }
          ]
        }
      ],
      "configurations": configurations
    }

    # only 1 partition, enough disk space, no warnings
    res = self.stackAdvisor.validateAmsHbaseSiteConfigurations(properties, recommendedDefaults, configurations, services, hosts)
    expected = []
    self.assertEquals(res, expected)


    # 1 partition, no enough disk space
    host['Hosts']['disk_info'] = [
      {
        "available" : '1',
        "type" : "ext4",
        "mountpoint" : "/"
      }
    ]
    res = self.stackAdvisor.validateAmsHbaseSiteConfigurations(properties, recommendedDefaults, configurations, services, hosts)
    expected = [
      {'config-name': 'hbase.rootdir',
       'config-type': 'ams-hbase-site',
       'level': 'WARN',
       'message': 'Ambari Metrics disk space requirements not met. '
                  '\nRecommended disk space for partition / is 10G',
       'type': 'configuration'
      }
    ]
    self.assertEquals(res, expected)

    # 2 partitions
    host['Hosts']['disk_info'] = [
      {
        "available": str(15<<30), # 15 GB
        "type" : "ext4",
        "mountpoint" : "/grid/0"
      },
      {
        "available" : str(15<<30), # 15 GB
        "type" : "ext4",
        "mountpoint" : "/"
      }
    ]
    recommendedDefaults = {
      'hbase.rootdir': 'file:///grid/0/var/lib/ambari-metrics-collector/hbase',
      'hbase.tmp.dir': '/var/lib/ambari-metrics-collector/hbase',
      'hbase.cluster.distributed': 'false'
    }
    properties = {
      'hbase.rootdir': 'file:///grid/0/var/lib/ambari-metrics-collector/hbase',
      'hbase.tmp.dir' : '/var/lib/ambari-metrics-collector/hbase',
      'hbase.cluster.distributed': 'false'
    }
    res = self.stackAdvisor.validateAmsHbaseSiteConfigurations(properties, recommendedDefaults, configurations, services, hosts)
    expected = []
    self.assertEquals(res, expected)

    # dfs.dir & hbase.rootdir crosscheck + root partition + hbase.rootdir == hbase.tmp.dir warnings
    properties = {
      'hbase.rootdir': 'file:///var/lib/ambari-metrics-collector/hbase',
      'hbase.tmp.dir' : '/var/lib/ambari-metrics-collector/hbase',
      'hbase.cluster.distributed': 'false'
    }

    res = self.stackAdvisor.validateAmsHbaseSiteConfigurations(properties, recommendedDefaults, configurations, services, hosts)
    expected = [
      {
        'config-name': 'hbase.rootdir',
        'config-type': 'ams-hbase-site',
        'level': 'WARN',
        'message': 'It is not recommended to use root partition for hbase.rootdir',
        'type': 'configuration'
      },
      {
        'config-name': 'hbase.tmp.dir',
        'config-type': 'ams-hbase-site',
        'level': 'WARN',
        'message': 'Consider not using / partition for storing metrics temporary data. '
                   '/ partition is already used as hbase.rootdir to store metrics data',
        'type': 'configuration'
      },
      {
        'config-name': 'hbase.rootdir',
        'config-type': 'ams-hbase-site',
        'level': 'WARN',
        'message': 'Consider not using / partition for storing metrics data. '
                   '/ is already used by datanode to store HDFS data',
        'type': 'configuration'
      }
    ]
    self.assertEquals(res, expected)

    # incorrect hbase.rootdir in distributed mode
    properties = {
      'hbase.rootdir': 'file:///grid/0/var/lib/ambari-metrics-collector/hbase',
      'hbase.tmp.dir' : '/var/lib/ambari-metrics-collector/hbase',
      'hbase.cluster.distributed': 'false'
    }
    configurations['ams-site']['properties']['timeline.metrics.service.operation.mode'] = 'distributed'
    res = self.stackAdvisor.validateAmsHbaseSiteConfigurations(properties, recommendedDefaults, configurations, services, hosts)
    expected = [
      {
        'config-name': 'hbase.rootdir',
        'config-type': 'ams-hbase-site',
        'level': 'WARN',
        'message': 'In distributed mode hbase.rootdir should point to HDFS.',
        'type': 'configuration'
      }
    ]
    self.assertEquals(res, expected)

  def test_validateStormSiteConfigurations(self):
    configurations = {
      "storm-site": {
        "properties": {
          'metrics.reporter.register': "org.apache.hadoop.metrics2.sink.storm.StormTimelineMetricsReporter"
        }
      }
    }

    recommendedDefaults = {
      'metrics.reporter.register': 'org.apache.hadoop.metrics2.sink.storm.StormTimelineMetricsReporter',
    }
    properties = {
      'metrics.reporter.register': 'org.apache.hadoop.metrics2.sink.storm.StormTimelineMetricsReporter',
    }

    services = {
      "services":  [
        {
          "StackServices": {
            "service_name": "AMBARI_METRICS"
          }
        }
      ],
      "configurations": configurations
    }

    # positive
    res = self.stackAdvisor.validateStormConfigurations(properties, recommendedDefaults, configurations, services, None)
    expected = []
    self.assertEquals(res, expected)
    properties['metrics.reporter.register'] = ''

    res = self.stackAdvisor.validateStormConfigurations(properties, recommendedDefaults, configurations, services, None)
    expected = [
      {'config-name': 'metrics.reporter.register',
       'config-type': 'storm-site',
       'level': 'WARN',
       'message': 'Should be set to org.apache.hadoop.metrics2.sink.storm.StormTimelineMetricsReporter '
                  'to report the metrics to Ambari Metrics service.',
       'type': 'configuration'
      }
    ]
    self.assertEquals(res, expected)

  def test_getHostsWithComponent(self):
    services = {"services":
                  [{"StackServices":
                      {"service_name" : "HDFS",
                       "service_version" : "2.6.0.2.2"
                      },
                    "components":[
                      {
                        "href":"/api/v1/stacks/HDP/versions/2.2/services/HDFS/components/DATANODE",
                        "StackServiceComponents":{
                          "advertise_version":"true",
                          "cardinality":"1+",
                          "component_category":"SLAVE",
                          "component_name":"DATANODE",
                          "custom_commands":[

                          ],
                          "display_name":"DataNode",
                          "is_client":"false",
                          "is_master":"false",
                          "service_name":"HDFS",
                          "stack_name":"HDP",
                          "stack_version":"2.2",
                          "hostnames":[
                            "host1",
                            "host2"
                          ]
                        },
                        "dependencies":[

                        ]
                      },
                      {
                        "href":"/api/v1/stacks/HDP/versions/2.2/services/HDFS/components/JOURNALNODE",
                        "StackServiceComponents":{
                          "advertise_version":"true",
                          "cardinality":"0+",
                          "component_category":"SLAVE",
                          "component_name":"JOURNALNODE",
                          "custom_commands":[

                          ],
                          "display_name":"JournalNode",
                          "is_client":"false",
                          "is_master":"false",
                          "service_name":"HDFS",
                          "stack_name":"HDP",
                          "stack_version":"2.2",
                          "hostnames":[
                            "host1"
                          ]
                        },
                        "dependencies":[
                          {
                            "href":"/api/v1/stacks/HDP/versions/2.2/services/HDFS/components/JOURNALNODE/dependencies/HDFS_CLIENT",
                            "Dependencies":{
                              "component_name":"HDFS_CLIENT",
                              "dependent_component_name":"JOURNALNODE",
                              "dependent_service_name":"HDFS",
                              "stack_name":"HDP",
                              "stack_version":"2.2"
                            }
                          }
                        ]
                      },
                      {
                        "href":"/api/v1/stacks/HDP/versions/2.2/services/HDFS/components/NAMENODE",
                        "StackServiceComponents":{
                          "advertise_version":"true",
                          "cardinality":"1-2",
                          "component_category":"MASTER",
                          "component_name":"NAMENODE",
                          "custom_commands":[
                            "DECOMMISSION",
                            "REBALANCEHDFS"
                          ],
                          "display_name":"NameNode",
                          "is_client":"false",
                          "is_master":"true",
                          "service_name":"HDFS",
                          "stack_name":"HDP",
                          "stack_version":"2.2",
                          "hostnames":[
                            "host2"
                          ]
                        },
                        "dependencies":[

                        ]
                      },
                      ],
                    }],
                "configurations": {}
    }
    hosts = {
      "items" : [
        {
          "href" : "/api/v1/hosts/host1",
          "Hosts" : {
            "cpu_count" : 1,
            "host_name" : "host1",
            "os_arch" : "x86_64",
            "os_type" : "centos6",
            "ph_cpu_count" : 1,
            "public_host_name" : "host1",
            "rack_info" : "/default-rack",
            "total_mem" : 2097152
          }
        },
        {
          "href" : "/api/v1/hosts/host2",
          "Hosts" : {
            "cpu_count" : 1,
            "host_name" : "host2",
            "os_arch" : "x86_64",
            "os_type" : "centos6",
            "ph_cpu_count" : 1,
            "public_host_name" : "host2",
            "rack_info" : "/default-rack",
            "total_mem" : 1048576
          }
        },
        ]
    }

    datanodes = self.stackAdvisor.getHostsWithComponent("HDFS", "DATANODE", services, hosts)
    self.assertEquals(len(datanodes), 2)
    self.assertEquals(datanodes, hosts["items"])
    datanode = self.stackAdvisor.getHostWithComponent("HDFS", "DATANODE", services, hosts)
    self.assertEquals(datanode, hosts["items"][0])
    namenodes = self.stackAdvisor.getHostsWithComponent("HDFS", "NAMENODE", services, hosts)
    self.assertEquals(len(namenodes), 1)
    # [host2]
    self.assertEquals(namenodes, [hosts["items"][1]])
    namenode = self.stackAdvisor.getHostWithComponent("HDFS", "NAMENODE", services, hosts)
    # host2
    self.assertEquals(namenode, hosts["items"][1])

    # not installed
    nodemanager = self.stackAdvisor.getHostWithComponent("YARN", "NODEMANAGER", services, hosts)
    self.assertEquals(nodemanager, None)

    # unknown component
    unknown_component = self.stackAdvisor.getHostWithComponent("YARN", "UNKNOWN", services, hosts)
    self.assertEquals(nodemanager, None)
    # unknown service
    unknown_component = self.stackAdvisor.getHostWithComponent("UNKNOWN", "NODEMANAGER", services, hosts)
    self.assertEquals(nodemanager, None)

  def test_mergeValidators(self):
    childValidators = {
      "HDFS": {"hdfs-site": "validateHDFSConfigurations2.3"},
      "HIVE": {"hiveserver2-site": "validateHiveServer2Configurations2.3"},
      "HBASE": {"hbase-site": "validateHBASEConfigurations2.3",
                "newconf": "new2.3"},
      "NEWSERVICE" : {"newserviceconf": "abc2.3"}
    }
    parentValidators = {
      "HDFS": {"hdfs-site": "validateHDFSConfigurations2.2",
               "hadoop-env": "validateHDFSConfigurationsEnv2.2"},
      "YARN": {"yarn-env": "validateYARNEnvConfigurations2.2"},
      "HIVE": {"hiveserver2-site": "validateHiveServer2Configurations2.2",
               "hive-site": "validateHiveConfigurations2.2",
               "hive-env": "validateHiveConfigurationsEnv2.2"},
      "HBASE": {"hbase-site": "validateHBASEConfigurations2.2",
                "hbase-env": "validateHBASEEnvConfigurations2.2"},
      "MAPREDUCE2": {"mapred-site": "validateMapReduce2Configurations2.2"},
      "TEZ": {"tez-site": "validateTezConfigurations2.2"}
    }
    expected = {
      "HDFS": {"hdfs-site": "validateHDFSConfigurations2.3",
               "hadoop-env": "validateHDFSConfigurationsEnv2.2"},
      "YARN": {"yarn-env": "validateYARNEnvConfigurations2.2"},
      "HIVE": {"hiveserver2-site": "validateHiveServer2Configurations2.3",
               "hive-site": "validateHiveConfigurations2.2",
               "hive-env": "validateHiveConfigurationsEnv2.2"},
      "HBASE": {"hbase-site": "validateHBASEConfigurations2.3",
                "hbase-env": "validateHBASEEnvConfigurations2.2",
                "newconf": "new2.3"},
      "MAPREDUCE2": {"mapred-site": "validateMapReduce2Configurations2.2"},
      "TEZ": {"tez-site": "validateTezConfigurations2.2"},
      "NEWSERVICE" : {"newserviceconf": "abc2.3"}
    }

    self.stackAdvisor.mergeValidators(parentValidators, childValidators)
    self.assertEquals(expected, parentValidators)

  def test_getProperMountPoint(self):
    hostInfo = None
    self.assertEquals(["/"], self.stackAdvisor.getPreferredMountPoints(hostInfo))
    hostInfo = {"some_key": []}
    self.assertEquals(["/"], self.stackAdvisor.getPreferredMountPoints(hostInfo))
    hostInfo["disk_info"] = []
    self.assertEquals(["/"], self.stackAdvisor.getPreferredMountPoints(hostInfo))
    # root mountpoint with low space available
    hostInfo["disk_info"].append(
      {
        "available" : "1",
        "type" : "ext4",
        "mountpoint" : "/"
      }
    )
    self.assertEquals(["/"], self.stackAdvisor.getPreferredMountPoints(hostInfo))
    # tmpfs with more space available
    hostInfo["disk_info"].append(
      {
        "available" : "2",
        "type" : "tmpfs",
        "mountpoint" : "/dev/shm"
      }
    )
    self.assertEquals(["/"], self.stackAdvisor.getPreferredMountPoints(hostInfo))
    # /boot with more space available
    hostInfo["disk_info"].append(
      {
        "available" : "3",
        "type" : "tmpfs",
        "mountpoint" : "/boot/grub"
      }
    )
    self.assertEquals(["/"], self.stackAdvisor.getPreferredMountPoints(hostInfo))
    # /boot with more space available
    hostInfo["disk_info"].append(
      {
        "available" : "4",
        "type" : "tmpfs",
        "mountpoint" : "/mnt/external_hdd"
      }
    )
    self.assertEquals(["/"], self.stackAdvisor.getPreferredMountPoints(hostInfo))
    # virtualbox fs with more space available
    hostInfo["disk_info"].append(
      {
        "available" : "5",
        "type" : "vboxsf",
        "mountpoint" : "/vagrant"
      }
    )
    self.assertEquals(["/"], self.stackAdvisor.getPreferredMountPoints(hostInfo))
    # proper mountpoint with more space available
    hostInfo["disk_info"].append(
      {
        "available" : "6",
        "type" : "ext4",
        "mountpoint" : "/grid/0"
      }
    )
    self.assertEquals(["/grid/0", "/"], self.stackAdvisor.getPreferredMountPoints(hostInfo))
    # proper mountpoint with more space available
    hostInfo["disk_info"].append(
      {
        "available" : "7",
        "type" : "ext4",
        "mountpoint" : "/grid/1"
      }
    )
    self.assertEquals(["/grid/1", "/grid/0", "/"], self.stackAdvisor.getPreferredMountPoints(hostInfo))

  def test_validateNonRootFs(self):
    hostInfo = {"disk_info": [
      {
        "available" : "2",
        "type" : "ext4",
        "mountpoint" : "/"
      }
    ]}
    properties = {"property1": "file:///var/dir"}
    recommendedDefaults = {"property1": "file:///var/dir"}
    # only / mountpoint - no warning
    self.assertTrue(self.stackAdvisor.validatorNotRootFs(properties, recommendedDefaults, 'property1', hostInfo) == None)
    # More preferable /grid/0 mountpoint - warning
    hostInfo["disk_info"].append(
      {
        "available" : "3",
        "type" : "ext4",
        "mountpoint" : "/grid/0"
      }
    )
    recommendedDefaults = {"property1": "file:///grid/0/var/dir"}
    warn = self.stackAdvisor.validatorNotRootFs(properties, recommendedDefaults, 'property1', hostInfo)
    self.assertFalse(warn == None)
    self.assertEquals({'message': 'It is not recommended to use root partition for property1', 'level': 'WARN'}, warn)

    # Set by user /var mountpoint, which is non-root , but not preferable - no warning
    hostInfo["disk_info"].append(
      {
        "available" : "1",
        "type" : "ext4",
        "mountpoint" : "/var"
      }
    )
    self.assertTrue(self.stackAdvisor.validatorNotRootFs(properties, recommendedDefaults, 'property1', hostInfo) == None)

  def test_validatorEnoughDiskSpace(self):
    reqiuredDiskSpace = 1048576
    errorMsg = "Ambari Metrics disk space requirements not met. \n" \
               "Recommended disk space for partition / is 1G"

    # local FS, enough space
    hostInfo = {"disk_info": [
      {
        "available" : "1048578",
        "type" : "ext4",
        "mountpoint" : "/"
      }
    ]}
    properties = {"property1": "file:///var/dir"}
    self.assertTrue(self.stackAdvisor.validatorEnoughDiskSpace(properties, 'property1', hostInfo, reqiuredDiskSpace) == None)

    # local FS, no enough space
    hostInfo = {"disk_info": [
      {
        "available" : "1",
        "type" : "ext4",
        "mountpoint" : "/"
      }
    ]}
    warn = self.stackAdvisor.validatorEnoughDiskSpace(properties, 'property1', hostInfo, reqiuredDiskSpace)
    self.assertTrue(warn != None)
    self.assertEquals({'message': errorMsg, 'level': 'WARN'}, warn)

    # non-local FS, HDFS
    properties = {"property1": "hdfs://h1"}
    self.assertTrue(self.stackAdvisor.validatorEnoughDiskSpace(properties, 'property1', hostInfo, reqiuredDiskSpace) == None)

    # non-local FS, WASB
    properties = {"property1": "wasb://h1"}
    self.assertTrue(self.stackAdvisor.validatorEnoughDiskSpace(properties, 'property1', hostInfo, reqiuredDiskSpace) == None)

  def test_round_to_n(self):
    self.assertEquals(self.stack_advisor_impl.round_to_n(0), 0)
    self.assertEquals(self.stack_advisor_impl.round_to_n(1000), 1024)
    self.assertEquals(self.stack_advisor_impl.round_to_n(2000), 2048)
    self.assertEquals(self.stack_advisor_impl.round_to_n(4097), 4096)

  def test_getMountPointForDir(self):
    self.assertEquals(self.stack_advisor_impl.getMountPointForDir("/var/log", ["/"]), "/")
    self.assertEquals(self.stack_advisor_impl.getMountPointForDir("/var/log", ["/var", "/"]), "/var")
    self.assertEquals(self.stack_advisor_impl.getMountPointForDir("file:///var/log", ["/var", "/"]), "/var")
    self.assertEquals(self.stack_advisor_impl.getMountPointForDir("hdfs:///hdfs_path", ["/var", "/"]), None)
    self.assertEquals(self.stack_advisor_impl.getMountPointForDir("relative/path", ["/var", "/"]), None)

  def test_getValidatorEqualsToRecommendedItem(self):
    properties = {"property1": "value1"}
    recommendedDefaults = {"property1": "value1"}
    self.assertEquals(self.stackAdvisor.validatorEqualsToRecommendedItem(properties, recommendedDefaults, "property1"), None)
    properties = {"property1": "value1"}
    recommendedDefaults = {"property1": "value2"}
    expected = {'message': 'It is recommended to set value value2 for property property1', 'level': 'WARN'}
    self.assertEquals(self.stackAdvisor.validatorEqualsToRecommendedItem(properties, recommendedDefaults, "property1"), expected)
    properties = {}
    recommendedDefaults = {"property1": "value2"}
    expected = {'level': 'ERROR', 'message': 'Value should be set for property1'}
    self.assertEquals(self.stackAdvisor.validatorEqualsToRecommendedItem(properties, recommendedDefaults, "property1"), expected)
    properties = {"property1": "value1"}
    recommendedDefaults = {}
    expected = {'level': 'ERROR', 'message': 'Value should be recommended for property1'}
    self.assertEquals(self.stackAdvisor.validatorEqualsToRecommendedItem(properties, recommendedDefaults, "property1"), expected)

  def test_getServicesSiteProperties(self):
    import imp, os
    testDirectory = os.path.dirname(os.path.abspath(__file__))
    hdp206StackAdvisorPath = os.path.join(testDirectory, '../../../../../main/resources/stacks/HDP/2.0.6/services/stack_advisor.py')
    stack_advisor = imp.load_source('stack_advisor', hdp206StackAdvisorPath)
    services = {
      "services":  [
        {
          "StackServices": {
            "service_name": "RANGER"
          },
          "components": [
            {
              "StackServiceComponents": {
                "component_name": "RANGER_ADMIN",
                "hostnames": ["host1"]
              }
            }
          ]
        },
        ],
      "configurations": {
        "admin-properties": {
          "properties": {
            "DB_FLAVOR": "NOT_EXISTING",
            }
        },
        "ranger-admin-site": {
          "properties": {
            "ranger.service.http.port": "7777",
            "ranger.service.http.enabled": "true",
            }
        }
      }
    }
    expected = {
      "ranger.service.http.port": "7777",
      "ranger.service.http.enabled": "true",
    }
    siteProperties = stack_advisor.getServicesSiteProperties(services, "ranger-admin-site")
    self.assertEquals(siteProperties, expected)

