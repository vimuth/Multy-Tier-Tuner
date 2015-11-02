import argparse
import re
import os
import httplib
import jvmtunerInterface
from jvmtunerInterface import JvmFlagsTunerInterface
import paramiko
import re
import logging

logging.getLogger("paramiko").setLevel(logging.WARNING)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def set_configuration(configuration):
    ssh.connect('10.8.106.245', username='cse',
        password='cse@123')
    stdin, stdout, stderr = ssh.exec_command('sudo -S sed -i -e \'s/JAVA_OPTS=\".*\"/JAVA_OPTS="'+  configuration   +'"/g\' /etc/default/tomcat7')
    stdin.write('cse@123\n')
    stdin.flush()

def set_ajp_configuration(configuration):
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

def set_apache2_configuration(configuration):
    ssh.connect('10.8.106.246', username='vimuthf',
        password='vimuth123')

    for flag in configuration.keys():
        stdin, stdout, stderr = ssh.exec_command('sudo -S sed -i -e \'s/'+ flag +'[[:space:]]*[0-9]*/'+ flag +' '+  str(configuration[flag])  +'/g\' /etc/apache2/mods-enabled/mpm_event.conf')
        stdin.write('vimuth123\n')
        stdin.flush()
        # output = stdout.read().splitlines()
        # print output, stderr

def set_mysql_configuration(configuration):
    ssh.connect('10.8.106.244', username='cse',
        password='cse@123')

    for flag in  configuration.keys():
        stdin, stdout, stderr = ssh.exec_command('sudo -S sed -i -r -e \'s/'+ flag +'[[:space:]]*=[[:space:]]*[0-9]*[M|K|G]?/'+ flag +' = '+  str(configuration[flag])  +'/g\' /etc/mysql/my.cnf ')
                                                #  'sudo -S sed -i -r -e \'s/'       +'[[:space:]]*=[[:space:]]*[0-9]*[M|K|G]?/key_buffer_size = 13M/g'
        stdin.write('cse@123\n')
        stdin.flush()


def restart_servers():
    print "Restarting servers..."
    ssh.connect('10.8.106.244', username='cse',
        password='cse@123')
    stdin, stdout, stderr = ssh.exec_command("sudo -S service mysql restart")
    stdin.write('cse@123\n')
    stdin.flush()
    output = stdout.read().splitlines()
    print output
    if 'fail' in output[-1] :
        return False

    ssh.connect('10.8.106.245', username='cse',
        password='cse@123')
    stdin, stdout, stderr = ssh.exec_command("sudo -S service tomcat7 restart")
    stdin.write('cse@123\n')
    stdin.flush()
    output = stdout.read().splitlines()
    print output
    if 'fail' in output[-1] :
        return False

    ssh.connect('10.8.106.246', username='vimuthf',
        password='vimuth123')
    # print stdout.read().splitlines(), stderr.read().splitlines()
    stdin, stdout, stderr = ssh.exec_command("sudo -S service apache2 restart")
    stdin.write('vimuth123\n')
    stdin.flush()
    output = stdout.read().splitlines()
    print output
    if 'fail' in output[-1] :
        return False

    return True

def health_check(host, path):
    try:
        conn = httplib.HTTPConnection(host)
        conn.request("HEAD", path)
        return conn.getresponse().status
    except StandardError:
        return None

def run_remote_sudo_command(host, username, password, command):
    try:
        ssh.connect(host, username=username, password=password)
        stdin, stdout, stderr = ssh.exec_command(command)
        stdin.write(password+'\n')
        stdin.flush()
        return stdout, stderr
    except StandardError:
        print "Error while executing command"
        return None

tomcat_jvm_configuration = "-XX:+UseParallelOldGC -XX:+ParallelGCVerbose -XX:ParallelGCThreads=9 -XX:ParallelGCBufferWastePct=6 -XX:-AlwaysTenure -XX:+NeverTenure -XX:+ScavengeBeforeFullGC -XX:-UseMaximumCompactionOnSystemGC -XX:ParallelOldDeadWoodLimiterMean=74 -XX:ParallelOldDeadWoodLimiterStdDev=87 -XX:+ResizePLAB -XX:+ResizeOldPLAB -XX:+AlwaysPreTouch -XX:-ParallelRefProcEnabled -XX:-ParallelRefProcBalancingEnabled -XX:+UseTLAB -XX:+ResizeTLAB -XX:-ZeroTLAB -XX:-FastTLABRefill -XX:-NeverActAsServerClassMachine -XX:+AlwaysActAsServerClassMachine -XX:-UseAutoGCSelectPolicy -XX:-UseAdaptiveSizePolicy -XX:+UsePSAdaptiveSurvivorSizePolicy -XX:-UseAdaptiveGenerationSizePolicyAtMinorCollection -XX:-UseAdaptiveGenerationSizePolicyAtMajorCollection -XX:-UseAdaptiveSizePolicyWithSystemGC -XX:-UseAdaptiveGCBoundary -XX:+UseAdaptiveSizePolicyFootprintGoal -XX:+UseAdaptiveSizeDecayMajorGCCost -XX:+UseGCOverheadLimit -XX:+PrintAdaptiveSizePolicy -XX:-DisableExplicitGC -XX:+CollectGen0First -XX:+BindGCTaskThreadsToCPUs -XX:+UseGCTaskAffinity -XX:YoungPLABSize=4476 -XX:OldPLABSize=660 -XX:GCTaskTimeStampEntries=201 -XX:TargetPLABWastePct=11 -XX:PLABWeight=75 -XX:OldPLABWeight=36 -XX:MarkStackSize=4783905 -XX:MarkStackSizeMax=642664546 -XX:RefDiscoveryPolicy=0 -XX:InitiatingHeapOccupancyPercent=53 -XX:MaxRAM=91448271572 -XX:ErgoHeapSizeLimit=0 -XX:MaxRAMFraction=3 -XX:DefaultMaxRAMFraction=6 -XX:MinRAMFraction=1 -XX:InitialRAMFraction=44 -XX:AutoGCSelectPauseMillis=7242 -XX:AdaptiveSizeThroughPutPolicy=0 -XX:AdaptiveSizePausePolicy=0 -XX:AdaptiveSizePolicyInitializingSteps=18 -XX:AdaptiveSizePolicyOutputInterval=0 -XX:AdaptiveSizePolicyWeight=6 -XX:AdaptiveTimeWeight=31 -XX:PausePadding=1 -XX:PromotedPadding=2 -XX:SurvivorPadding=4 -XX:AdaptivePermSizeWeight=25 -XX:PermGenPadding=1 -XX:ThresholdTolerance=7 -XX:AdaptiveSizePolicyCollectionCostMargin=65 -XX:YoungGenerationSizeIncrement=13 -XX:YoungGenerationSizeSupplement=92 -XX:YoungGenerationSizeSupplementDecay=10 -XX:TenuredGenerationSizeIncrement=24 -XX:TenuredGenerationSizeSupplement=65 -XX:TenuredGenerationSizeSupplementDecay=2 -XX:MaxGCPauseMillis=10414310295555726913 -XX:GCPauseIntervalMillis=0 -XX:MaxGCMinorPauseMillis=27226593838715484247 -XX:GCTimeRatio=96 -XX:AdaptiveSizeDecrementScaleFactor=4 -XX:AdaptiveSizeMajorGCDecayTimeScale=12 -XX:MinSurvivorRatio=3 -XX:InitialSurvivorRatio=8 -XX:BaseFootPrintEstimate=209590576 -XX:GCTimeLimit=75 -XX:GCHeapFreeLimit=2 -XX:PrefetchCopyIntervalInBytes=590 -XX:PrefetchScanIntervalInBytes=794 -XX:PrefetchFieldsAhead=0 -XX:ProcessDistributionStride=4 -XX:+UseCompiler -XX:+UseCounterDecay -XX:+AlwaysCompileLoopMethods -XX:-DontCompileHugeMethods -XX:-TieredCompilation -XX:CompileThreshold=9563 -XX:BackEdgeThreshold=71709 -XX:OnStackReplacePercentage=189 -XX:InterpreterProfilePercentage=36"

tomcat_ajp_configuration = {'AJP_maxThreads': 1247, 'AJP_acceptCount': 1729, 'AJP_acceptorThreadCount': 201, 'AJP_minSpareThreads': 1337}

apache2_configuration = {'MaxConnectionsPerChild': 227, 'StartServers': 138, 'MinSpareThreads': 389, 'MaxSpareThreads': 1, 'ThreadLimit': 26, 'MaxRequestWorkers': 207, 'ThreadsPerChild': 142}

mysql_configuration = {'table_cache': 368734, 'innodb_buffer_pool_size': 6208600095, 'query_cache_size': 2015574160, 'sort_buffer_size': 4189236462, 'max_allowed_packet': 702303920, 'thread_stack': 2549937471, 'query_cache_limit': 1123461093, 'read_buffer_size': 2291709590, 'max_connections': 56012, 'thread_cache_size': 8734, 'key_buffer_size': 3199125954, 'max_connect_errors': 8410}

set_configuration(tomcat_jvm_configuration)
set_ajp_configuration(tomcat_ajp_configuration)
set_apache2_configuration(apache2_configuration)
set_mysql_configuration(mysql_configuration)
restart_servers()
