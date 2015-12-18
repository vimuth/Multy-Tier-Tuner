import argparse
import re
import os
import httplib
import jvmtunerInterface
from jvmtunerInterface import JvmFlagsTunerInterface
import paramiko
import re
import logging
import sys

default_tomcat_jvm_configuration = ""
default_tomcat_ajp_configuration = {'AJP_maxThreads': 200, 'AJP_acceptCount': 100, 'AJP_acceptorThreadCount': 1, 'AJP_minSpareThreads': 10}
default_apache2_configuration = {'MaxConnectionsPerChild': 0, 'StartServers': 2, 'MinSpareThreads': 25, 'MaxSpareThreads': 75, 'ThreadLimit': 64, 'MaxRequestWorkers': 150, 'ThreadsPerChild': 25}
default_mysql_configuration = {'table_cache': 64, 'innodb_buffer_pool_size': 134217728, 'query_cache_size': 16777216, 'sort_buffer_size': 2097144, 'max_allowed_packet': 16777216, 'thread_stack': 196608, 'query_cache_limit': 1048576, 'read_buffer_size': 131072, 'max_connections': 100, 'thread_cache_size': 0, 'key_buffer_size': 8388608, 'max_connect_errors': 10}

logging.getLogger("paramiko").setLevel(logging.WARNING)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def set_tomcat_configuration(jvm_configuration, configuration):
    ssh.connect('10.8.106.245', username='cse',
        password='cse@123')
    configuration_string = ""
    for flag in  configuration.keys():
        configuration_string = configuration_string + flag[4:] + "=\"" + str(configuration[flag]) + "\" "
    escaped = configuration_string.replace('"','\\"')
    configuration_string = '<Connector port=\\"8009\\" protocol=\\"AJP\\/1.3\\" '+ escaped +'\\/>'
    stdin, stdout, stderr = ssh.exec_command('sudo -S sed -i -e \'s/<Connector port=\\"8009\\".*/'+ configuration_string + '/g\' /var/lib/tomcat7/conf/server.xml')
    # print stdout.read().splitlines()
    stdin.write('cse@123\n')                 #sudo sed -i -e \'s/<Connector port=\"8009\  ".*/AAAAAAAAA/g' /var/lib/tomcat7/conf/server.xml
    stdin.flush()
    stdin, stdout, stderr = ssh.exec_command('sudo -S sed -i -e \'s/JAVA_OPTS=\".*\"/JAVA_OPTS="'+  jvm_configuration   +'"/g\' /etc/default/tomcat7')
    stdin.write('cse@123\n')
    stdin.flush()
    stdin, stdout, stderr = ssh.exec_command("sudo -S service tomcat7 restart")
    stdin.write('cse@123\n')
    stdin.flush()
    output = stdout.read().splitlines()
    ssh.close()
    print output
    if 'fail' in output[-1] :
        return False

def set_apache2_configuration(configuration):
    ssh.connect('10.8.106.246', username='vimuthf',
        password='vimuth123')

    for flag in configuration.keys():
        stdin, stdout, stderr = ssh.exec_command('sudo -S sed -i -e \'s/'+ flag +'[[:space:]]*[0-9]*/'+ flag +' '+  str(configuration[flag])  +'/g\' /etc/apache2/mods-enabled/mpm_event.conf')
        stdin.write('vimuth123\n')
        stdin.flush()
        # output = stdout.read().splitlines()
        # print output, stderr
    stdin, stdout, stderr = ssh.exec_command("sudo -S service apache2 restart")
    stdin.write('vimuth123\n')
    stdin.flush()
    output = stdout.read().splitlines()
    print output
    ssh.close()
    if 'fail' in output[-1] :
        return False
    return True

def set_mysql_configuration(configuration):
    ssh.connect('10.8.106.244', username='cse',
        password='cse@123')

    for flag in  configuration.keys():
        stdin, stdout, stderr = ssh.exec_command('sudo -S sed -i -r -e \'s/'+ flag +'[[:space:]]*=[[:space:]]*[0-9]*[M|K|G]?/'+ flag +' = '+  str(configuration[flag])  +'/g\' /etc/mysql/my.cnf ')
                                                #  'sudo -S sed -i -r -e \'s/'       +'[[:space:]]*=[[:space:]]*[0-9]*[M|K|G]?/key_buffer_size = 13M/g'
        stdin.write('cse@123\n')
        stdin.flush()
    stdin, stdout, stderr = ssh.exec_command("sudo -S service mysql restart")
    stdin.write('cse@123\n')
    stdin.flush()
    output = stdout.read().splitlines()
    print output
    ssh.close()
    if 'fail' in output[-1] :
        return False

tomcat_jvm_configuration = "-XX:+UseParallelGC -XX:+ParallelGCVerbose -XX:ParallelGCThreads=4 -XX:ParallelGCBufferWastePct=7 -XX:-AlwaysTenure -XX:-NeverTenure -XX:-ScavengeBeforeFullGC -XX:-UseParallelOldGC -XX:+ResizePLAB -XX:-ResizeOldPLAB -XX:-AlwaysPreTouch -XX:+ParallelRefProcEnabled -XX:-ParallelRefProcBalancingEnabled -XX:+UseTLAB -XX:-ResizeTLAB -XX:-ZeroTLAB -XX:-FastTLABRefill -XX:-NeverActAsServerClassMachine -XX:+AlwaysActAsServerClassMachine -XX:+UseAutoGCSelectPolicy -XX:+UseAdaptiveSizePolicy -XX:+UsePSAdaptiveSurvivorSizePolicy -XX:-UseAdaptiveGenerationSizePolicyAtMinorCollection -XX:-UseAdaptiveGenerationSizePolicyAtMajorCollection -XX:-UseAdaptiveSizePolicyWithSystemGC -XX:+UseAdaptiveGCBoundary -XX:-UseAdaptiveSizePolicyFootprintGoal -XX:-UseAdaptiveSizeDecayMajorGCCost -XX:+UseGCOverheadLimit -XX:-PrintAdaptiveSizePolicy -XX:-DisableExplicitGC -XX:+CollectGen0First -XX:-BindGCTaskThreadsToCPUs -XX:+UseGCTaskAffinity -XX:YoungPLABSize=3983 -XX:OldPLABSize=1258 -XX:GCTaskTimeStampEntries=296 -XX:TargetPLABWastePct=5 -XX:PLABWeight=54 -XX:OldPLABWeight=41 -XX:MarkStackSize=3942500 -XX:MarkStackSizeMax=422051824 -XX:RefDiscoveryPolicy=0 -XX:InitiatingHeapOccupancyPercent=37 -XX:MaxRAM=81822793012 -XX:ErgoHeapSizeLimit=0 -XX:MaxRAMFraction=4 -XX:DefaultMaxRAMFraction=5 -XX:MinRAMFraction=1 -XX:InitialRAMFraction=79 -XX:AutoGCSelectPauseMillis=4257 -XX:AdaptiveSizeThroughPutPolicy=0 -XX:AdaptiveSizePausePolicy=0 -XX:AdaptiveSizePolicyInitializingSteps=15 -XX:AdaptiveSizePolicyOutputInterval=0 -XX:AdaptiveSizePolicyWeight=15 -XX:AdaptiveTimeWeight=18 -XX:PausePadding=0 -XX:PromotedPadding=4 -XX:SurvivorPadding=2 -XX:AdaptivePermSizeWeight=19 -XX:PermGenPadding=2 -XX:ThresholdTolerance=6 -XX:AdaptiveSizePolicyCollectionCostMargin=58 -XX:YoungGenerationSizeIncrement=29 -XX:YoungGenerationSizeSupplement=60 -XX:YoungGenerationSizeSupplementDecay=10 -XX:TenuredGenerationSizeIncrement=13 -XX:TenuredGenerationSizeSupplement=67 -XX:TenuredGenerationSizeSupplementDecay=3 -XX:MaxGCPauseMillis=12365858181409294336 -XX:GCPauseIntervalMillis=0 -XX:MaxGCMinorPauseMillis=21818952507394621440 -XX:GCTimeRatio=121 -XX:AdaptiveSizeDecrementScaleFactor=2 -XX:AdaptiveSizeMajorGCDecayTimeScale=15 -XX:MinSurvivorRatio=3 -XX:InitialSurvivorRatio=6 -XX:BaseFootPrintEstimate=296911893 -XX:GCTimeLimit=75 -XX:GCHeapFreeLimit=1 -XX:PrefetchCopyIntervalInBytes=704 -XX:PrefetchScanIntervalInBytes=296 -XX:PrefetchFieldsAhead=1 -XX:ProcessDistributionStride=2 -XX:+UseCompiler -XX:+UseCounterDecay -XX:+AlwaysCompileLoopMethods -XX:-DontCompileHugeMethods -XX:-TieredCompilation -XX:CompileThreshold=9807 -XX:BackEdgeThreshold=145509 -XX:OnStackReplacePercentage=124 -XX:InterpreterProfilePercentage=23"

tomcat_ajp_configuration = {'AJP_maxThreads': 9996, 'AJP_acceptCount': 9537, 'AJP_acceptorThreadCount': 211, 'AJP_minSpareThreads': 1351}

apache2_configuration = {'MaxConnectionsPerChild': 382, 'StartServers': 338, 'MinSpareThreads': 363, 'MaxSpareThreads': 135, 'ThreadLimit': 229, 'MaxRequestWorkers': 368, 'ThreadsPerChild': 52}

mysql_configuration = {'table_cache': 264280, 'innodb_buffer_pool_size': 5892647301, 'query_cache_size': 2875141850, 'sort_buffer_size': 3945335738, 'max_allowed_packet': 32041091, 'thread_stack': 4222596274, 'query_cache_limit': 1488145297, 'read_buffer_size': 3788829642, 'max_connections': 7951, 'thread_cache_size': 9401, 'key_buffer_size': 3318407259, 'max_connect_errors': 3527}

if len(sys.argv)==2:
    print "Setting the default configuration"
    try:
        set_tomcat_configuration(default_tomcat_jvm_configuration, default_tomcat_ajp_configuration)
        set_apache2_configuration(default_apache2_configuration)
        set_mysql_configuration(default_mysql_configuration)
        print "Configuration Completed"
    finally:
        if ssh:
            ssh.close()
    sys.exit(0)

try:
    set_tomcat_configuration(tomcat_jvm_configuration, tomcat_ajp_configuration)
    set_apache2_configuration(apache2_configuration)
    set_mysql_configuration(mysql_configuration)
    print "Configuration Completed"
finally:
    if ssh:
        ssh.close()
sys.exit(0)
