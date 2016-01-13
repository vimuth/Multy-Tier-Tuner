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

argparser = argparse.ArgumentParser(parents=[jvmtunerInterface.argparser])
argparser.add_argument('--path',default='',help='benchmark path e.g KMEANS/')
argparser.add_argument('--np',default='10',help='Number of places ; default=10')
argparser.add_argument('--main',default='',help='Main class in the .jar file')
argparser.add_argument('--other',default='',help='Other Parameters needed by the jar file. ')

class MultiTierTuner(JvmFlagsTunerInterface):

    def __init__(self, *pargs, **kwargs):
        super(MultiTierTuner, self).__init__(args, *pargs,
                                        **kwargs)

    def execute_program(self):
        self.tuner_iterations+=1
        print "#######################################################################################################"
        print "Starting iteration ", self.tuner_iterations

        # print "\\n"
        print "The following configuration was used : "

        temp_metric = 0
        args.iterations=1;

        if 'apache' in self.tune:
            print self.apache_flag_configuration
            result = self.set_apache2_configuration(self.flags)
            if result==False:
                print "Configuration Failed while restarting the Apache servers!"
                return -1

        if 'mysql' in self.tune:
            print self.mysql_flag_configuration
            result = self.set_mysql_configuration(self.flags)
            if result==False:
                print "Configuration Failed while restarting the MySQl servers!"
                return -1

        if 'tomcat' in self.tune:
            print self.ajp_flag_configuration
            result = self.set_ajp_configuration(self.flags)
            if result==False:
                print "Configuration Failed while restarting the Tomcat servers!"
                return -1

        if 'tomcat_jvm' in self.tune:
            print self.flags
            result = self.set_configuration(self.flags)
            if result==False:
                print "Configuration Failed while restarting the Tomcat servers!"
                return -1

    	# if not self.restart_servers():
        #     print "Configuration Failed while restarting the servers!"
        #     return -1

    	health = self.health_check('10.8.106.246', '/tpcw/servlet/TPCW_home_interaction')
        if health!=200:
            print "Health check Failed with code -> ",health
            return -1
	else:
	    print "Health check passed with code -> ",health

        print "Benchmark running :\n"

        for i in range(0,int(args.iterations)):
            # if self.runtime_limit>0:
            #     print 'Execution with run time limit...'
            #run_result = self.call_program('ab -n 1000 -c10 -g result.dat "http://10.8.106.246/rubis_servlets/servlet/edu.rice.rubis.servlets.SearchItemsByCategory?category=1&categoryName=Antiques+%26+Art+&page=0&nbOfItems=25"', limit=100)
	    run_result = self.call_program('java -mx512M -cp .:/home/milinda/tpcw1.0\ 4 rbe.RBE -EB rbe.EBTPCW1Factory 400 -OUT browsing.m -RU 25 -MI 50 -RD 25 -WWW http://10.8.106.246/tpcw/ -CUST 144000 -ITEM 10000 -TT 1.0 -MAXERROR 0', limit=200)
            # else:
            #     run_result = self.call_program('ab -n 100 -c5 http://10.8.106.245:8080/rubis_servlets/')
            # print self.get_ms_x10benchmark(run_result['stdout'])
            temp_metric += self.getExecutionResut(run_result['stdout'])
            #print run_result
        temp_metric= float(temp_metric/int(args.iterations))
    	print "Results for this Iteration : ", temp_metric
    	print "#######################################################################################################"
        return temp_metric

    def getExecutionResut(self,result):
        print result
        # Getting the average
        # m=re.search('Time per request:[\s]*[0-9]*.[0-9]*[\s]*\[ms\][\s]*\(mean\)',result,flags=re.DOTALL)

        # Getting the min
        # m=re.search('100%[\s]*[0-9]*[\s]*\(longest request\)',result,flags=re.DOTALL)
	m=re.search('Average Response Time : [0-9.]*',result,flags=re.DOTALL)

        # print m
        m_sec=-1
        if m:
            m_sec=m.group(0)
            #Getting the average
            # m_sec=re.sub('Time per request:       ','',m_sec)
            # m_sec=re.sub('[\s]*\[ms\][\s]*\(mean\)','',m_sec)
            m_sec=re.sub('Average Response Time : ','',m_sec)
	    #m_sec=re.sub('100%[\s]*','',m_sec)
            #m_sec=re.sub('\(longest request\)','',m_sec)
        try:
            m_sec=float(m_sec)
        except:
            m_sec=-1
        return m_sec

    def set_configuration(self, configuration):
        ssh.connect('10.8.106.245', username='cse',
            password='cse@123')
        stdin, stdout, stderr = ssh.exec_command('sudo -S sed -i -e \'s/JAVA_OPTS=\".*\"/JAVA_OPTS="'+  configuration   +'"/g\' /etc/default/tomcat7')
        stdin.write('cse@123\n')
        stdin.flush()

        stdin, stdout, stderr = ssh.exec_command("sudo -S service tomcat7 restart")
        stdin.write('cse@123\n')
        stdin.flush()
        output = stdout.read().splitlines()
        print output
        if 'fail' in output[-1] :
            return False
        return True


    def set_ajp_configuration(self, configuration):
        ssh.connect('10.8.106.245', username='cse',
            password='cse@123')
        configuration_string = ""
        for flag in  self.ajp_flag_configuration.keys():
            configuration_string = configuration_string + flag[4:] + "=\"" + str(self.ajp_flag_configuration[flag]) + "\" "
        # configuration_string = '<Connector port=\\"8009\\" ' + configuration_string + "\\/>"
        escaped = configuration_string.replace('"','\\"')
        configuration_string = '<Connector port=\\"8009\\" protocol=\\"AJP\\/1.3\\" '+ escaped +'\\/>'
        # print configuration_string
        # print escaped
        stdin, stdout, stderr = ssh.exec_command('sudo -S sed -i -e \'s/<Connector port=\\"8009\\".*/'+ configuration_string + '/g\' /var/lib/tomcat7/conf/server.xml')
        # print stdout.read().splitlines()
        stdin.write('cse@123\n')                 #sudo sed -i -e \'s/<Connector port=\"8009\  ".*/AAAAAAAAA/g' /var/lib/tomcat7/conf/server.xml
        stdin.flush()
                # print stdout.read().splitlines()

        # output = stdout.read().splitlines()
        # print output, stderr
        # print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"

    def set_apache2_configuration(self, configuration):
        ssh.connect('10.8.106.246', username='vimuthf',
            password='vimuth123')

        for flag in  self.apache_flag_configuration.keys():
            stdin, stdout, stderr = ssh.exec_command('sudo -S sed -i -e \'s/'+ flag +'[[:space:]]*[0-9]*/'+ flag +' '+  str(self.apache_flag_configuration[flag])  +'/g\' /etc/apache2/mods-enabled/mpm_event.conf')
            stdin.write('vimuth123\n')
            stdin.flush()
            # output = stdout.read().splitlines()
            # print output, stderr
        stdin, stdout, stderr = ssh.exec_command("sudo -S service apache2 restart")
        stdin.write('vimuth123\n')
        stdin.flush()
        output = stdout.read().splitlines()
        print output
        if 'fail' in output[-1] :
            return False
        return True

    def set_mysql_configuration(self, configuration):
        ssh.connect('10.8.106.244', username='cse',
            password='cse@123')

        for flag in  self.mysql_flag_configuration.keys():
            stdin, stdout, stderr = ssh.exec_command('sudo -S sed -i -r -e \'s/'+ flag +'[[:space:]]*=[[:space:]]*[0-9]*[M|K|G]?/'+ flag +' = '+  str(self.mysql_flag_configuration[flag])  +'/g\' /etc/mysql/my.cnf ')
                                                    #  'sudo -S sed -i -r -e \'s/'       +'[[:space:]]*=[[:space:]]*[0-9]*[M|K|G]?/key_buffer_size = 13M/g'
            stdin.write('cse@123\n')
            stdin.flush()

        print "Restarting servers..."
        stdin, stdout, stderr = ssh.exec_command("sudo -S service mysql restart")
        stdin.write('cse@123\n')
        stdin.flush()
        output = stdout.read().splitlines()
        print output
        if 'fail' in output[-1] :
            return False
        return True

    def restart_servers(self):
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

    def health_check(self, host, path):
        try:
            conn = httplib.HTTPConnection(host, timeout=30)
            conn.request("HEAD", path)
            return conn.getresponse().status
        except StandardError, e:
            print e
	    return "Other Error"

    def run_remote_sudo_command(self, host, username, password, command):
        try:
            ssh.connect(host, username=username, password=password)
            stdin, stdout, stderr = ssh.exec_command(command)
            stdin.write(password+'\n')
            stdin.flush()
            return stdout, stderr
        except StandardError, e:
            print "Error while executing command"
	    print e
            return None


if __name__ == '__main__':
    args = argparser.parse_args()
    MultiTierTuner.main(args)
