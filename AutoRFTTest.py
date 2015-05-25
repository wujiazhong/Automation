import os,re,shutil
import time, datetime
import copy

from TestInfo import MAIN_VERSION_INDEX
from TestInfo import TestInfo
from TestInfo import KEY_WORD_LIST
from TestInfo import NO_STATS_INSTALLED

from SendEmail import SendEmail

#report summary path information
SUMMARY_FILE_NAME = "results_summary.txt"
VERSION_DIRECTORY = [r"\\svs1bo01","Stats","builds","outputs","statisticsmedia"]
SUMMARY_DIRECTORY = ["reports","VC9_64","client"]

#build directory information
BUILD_RELATIVE_DIR = ["Client","Statistics", "dvd_WinClient"]
LOCAL_BUILD_SAVING_PATH = ["C:\\" ,"test"]

#target keyword in BVT summary_report
IDENTICAL = "Identical"

#error msg
ERROR_MSG_LOGIN = "Fail to log in!"
ERROR_MSG_NO_FILE = "Fail to open the file. Please check if the file exists!"
ERROR_MSG_NO_REQUIRED_VERSION = "Please check the version directory. No matched version requested is found!"

#identical threshold
PASS_THRESHOLD = 0.8*100

#Silent install arguments
MSI_EXE = r"C:\Windows\System32\msiexec.exe"
INSTALL_DIR = ["C:\\" ,"Statistics","RFT_test"] 
STATS_MSI = ["Windows","SPSSStatistics","win64","IBM SPSS Statistics {VINDX}.msi"]

#rft.bat
RFT_BAT=r"_runRFT.bat"

#rft test result
RFT_TEST_REPORT = r"C:\Public\SVTOut\SVT_Summary_Report.txt"

#Time
ONE_HOUR = 3600
ONE_MIN = 60

FAIL = "Failed"
SUCCESS = "Succeeded"
    
def isPassTest():
    fp = open(g_absolute_report_dir, 'r') 
    file_content = fp.read() 
    #find the second float number between word 'Identical' and symbol '%' 
    try: 
        Matched_Info_List = re.findall(IDENTICAL+"\s+\d+\s+(.+?)\s+\%\n",file_content,re.S)
        if len(Matched_Info_List)<1:
            raise Exception("Cannot find keyword 'Identical' in the file. Please check the file!")
        if len(Matched_Info_List)>1:
            raise Exception("Too many keyword 'Identical' are matched. Please check the file!")
    except Exception:
        print("Report summary file does not has or has too much keyword matched 'Identical'")
        subject="Stats Client "+'.'.join(g_latest_build_index.split('.')[0:-1])+" [VC9_64] ("+g_latest_build_index+")"
        g_email_sender.sendEmail(g_latest_build_index, subject,"Report summary file does not has or has too much keyword matched 'Identical'. \
                                                        The report summary file is in "+g_absolute_report_dir+". Please check it!", FAIL)
        fp.close()
        return False
     
    Identical_Info = Matched_Info_List[0]
    #print Identical_Info
    fp.close()

    global log
    if float(Identical_Info)>=PASS_THRESHOLD and float(Identical_Info)<=100.0:
        log+=("Identical rate is more than 80%, so BVT passed...\n")
        print("BVT passed")
        return True
    else:
        log+=("Identical rate is less than 80%, so BVT did not pass...\n")
        print("BVT did not pass")
        subject="Stats Client "+'.'.join(g_latest_build_index.split('.')[0:-1])+" [VC9_64] ("+g_latest_build_index+")"
        g_email_sender.sendEmail(g_latest_build_index,subject, "Identical rate is less than 80%, so BVT did not pass. \
                                                        The report summary file is in "+g_absolute_report_dir+". Please check it!", FAIL)
        return False
        
def installNewBuild(main_version_index,has_run_rft_today):
    global log 
    if isPassTest():
        des_dir = os.path.join(*(LOCAL_BUILD_SAVING_PATH+[g_latest_build_index]))
            
        #download new version 
        log+=("Start to download latest build...\n")
        print("Start to download new build...")
        shutil.copytree(g_absolute_build_dir,des_dir)
        log+=("Complete downloading latest build...\n")
        print("Complete downloading...")
        
        #uninstall old version
        recent_test_build_index = test_info_table.getRecentTestBuildIndex()
        if recent_test_build_index != NO_STATS_INSTALLED:
            if not uninstallStats(recent_test_build_index):
                return False
              
        #install new version
        if not installStats(main_version_index):
            return False 
        
        #conduct rft 
        if not conductRFT(has_run_rft_today):
            return False
        
        #pass the build_index as an argument
        if os.path.isdir(des_dir):
            os.system(r"C:\Windows\System32\attrib -r "+ des_dir+"\*.* " + " /s")
            log+=("Start to delete old download build...\n")
            shutil.rmtree(des_dir, ignore_errors = True)
            log+=("Complete deleting old download build...\n")
        return True       
        
    else:
        #TO DO
        log+=("The installation failed since BVT test did not pass!\n")
        log+=("**************************\n\n")
        return False

def conductRFT(has_run_rft_today):
    global log
    global g_latest_build_index
    
    #enable Stats JVM
    #copy RFTJar to <install>\JRE\lib\ext
    print("Start to enable Stats JVM...")
    rft_jre_dir = os.path.join(*(INSTALL_DIR+["JRE","lib","ext"]))
    os.system(r"C:\Windows\System32\attrib -r "+ rft_jre_dir + " /s /d")
    os.system("copy "+"\""+test_info_table.rft_info_list[1]+ "\" "+rft_jre_dir)
    
    #copy RFT_Property to <install>\JRE\lib
    rft_property_dir = os.path.join(*(INSTALL_DIR+["JRE","lib"]))
    os.system(r"C:\Windows\System32\attrib -r "+ rft_property_dir+"\\accessibility.properties" + " /s")
    os.system("copy "+test_info_table.rft_info_list[2]+" "+rft_property_dir)
    log+=("Complete enabling Stats JVM...\n")
    print("Complete enabling Stats JVM...")

            
    #modify SVT properties file (SVT_Property): StatsVersion=<SPSS version> and TestBuild=23.0.1.0.35
    main_indx = g_latest_build_index.split('.')[0]
    stats_version_msg = "StatsVersion="+main_indx
    modifyFileContent(test_info_table.rft_info_list[3], "StatsVersion=\d{2}", stats_version_msg)
    modifyFileContent(test_info_table.rft_info_list[3], "TestBuild=\d{2}(\.\d){3}\.(\d{1,3})", "TestBuild="+g_latest_build_index)
    
    #modify Regression properties file (Reg_Property): IntialSettings.StatVersion=<SPSS version> and IntialSettings.Alert=IBM SPSS Statistics 23
    init_version_msg = "IntialSettings.StatVersion="+main_indx
    modifyFileContent(test_info_table.rft_info_list[4], "IntialSettings.StatVersion=\d{2}", init_version_msg)
    alert_msg="IntialSettings.Alert=IBM SPSS Statistics "+main_indx
    modifyFileContent(test_info_table.rft_info_list[4], "IntialSettings.Alert=IBM SPSS Statistics \d{2}", alert_msg)
            
    #conduct RFT 
    #execute SVTLocation\_runRFT.bat
    print("Start to execute RFT script...")
    os.system('\\'.join(test_info_table.rft_info_list[0].split("\\")+[RFT_BAT]))
    has_run_rft_today[0]=True
    
    #check the RFT report(C:\Public\SVTOut\SVT_Summary_Report.txt) every 10 minutes upto 3 hours, if it exist means the test complete, 
    #after check the file it exist, it should be sleep 1 minutes to
    incre_time = 10*ONE_MIN
    max_wait_time = 3*ONE_HOUR
    consume_time = 0
    subject = "RFT test on Stats Client "+'.'.join(g_latest_build_index.split('.')[0:-1])+" [VC9_64] ("+g_latest_build_index+")"
    #make sure all the info is written. Then send this file as attachment in email.
    is_rft_success = False
    while True: 
        if os.path.isfile(RFT_TEST_REPORT):
            time.sleep(ONE_MIN)
            rft_report_fp = open(RFT_TEST_REPORT, 'r')
            email_content = rft_report_fp.read()
            g_email_sender.sendEmail(g_latest_build_index,subject,email_content,SUCCESS)
            test_info_table.setRecentTestBuildIndex(g_latest_build_index)
            is_rft_success = True
            log+=("Complete RFT test for "+g_latest_build_index+"\n")
            print("Complete RFT test for "+g_latest_build_index)
            break
        elif consume_time <= max_wait_time:
            time.sleep(incre_time)
            consume_time += incre_time
            continue
        else:
            g_email_sender.sendEmail(g_latest_build_index,subject,"The RFT report summary did not exist! Please check the file path"+RFT_TEST_REPORT,FAIL)
            log+=("RFT test failed for no summary report generated...\n")
            print("RFT test failed for no summary report generated...")
            break
    
    return is_rft_success
    
def modifyFileContent(file_path, old_content_regression, new_content):
    os.system(r"C:\Windows\System32\attrib -r "+ file_path  + " /s")
    fp_svt_property = open(file_path, 'r')
    fp_svt_property_content = fp_svt_property.read()
    fp_svt_property_content = re.sub(old_content_regression, new_content, fp_svt_property_content)
    fp_svt_property.close()
    fp_svt_property = open(file_path, 'w+')
    fp_svt_property.write(fp_svt_property_content)
    fp_svt_property.close()
    
def sortVersionList(version_dir_list):
    i=0
    while i<len(version_dir_list):
        j=len(version_dir_list)-1
        while j>i:
            if int(version_dir_list[j].split('.')[-1]) > int(version_dir_list[j-1].split('.')[-1]):
                temp = version_dir_list[j]
                version_dir_list[j] = version_dir_list[j-1]
                version_dir_list[j-1] = temp
            j-=1
        i+=1
    return version_dir_list
                
def hasNewBuild(main_version_index):    
    path = os.path.join(*VERSION_DIRECTORY)
    build_list = list()
    for item in os.listdir(path):
        #e.g. main_version_index = 23.0.0.1
        #build_list consists of all sub-build under this main_version
        if re.match("(^"+main_version_index+"\.\d{1,3}$)", item):
            build_list.append(item)
           
    #sort the build_list from largest to smallest
    last_test_build_index = test_info_table.getLatestBuildNo(main_version_index) 
    build_list = sortVersionList(build_list)
    hasNewBuild = False
    for item in build_list:
        if int(item.split('.')[-1]) > int(last_test_build_index.split('.')[-1]):
            global g_latest_build_index 
            global g_absolute_report_dir
            global g_absolute_build_dir

            g_latest_build_index = item
            g_absolute_report_dir = os.path.join(*(VERSION_DIRECTORY+[g_latest_build_index]+SUMMARY_DIRECTORY+[SUMMARY_FILE_NAME]))  
            if os.path.isfile(g_absolute_report_dir):        
                g_absolute_build_dir= os.path.join(*(VERSION_DIRECTORY+[g_latest_build_index]+BUILD_RELATIVE_DIR))
                hasNewBuild = True
                break
        else:
            break
    
    print("Has new build: ",hasNewBuild)            
    return hasNewBuild

def getSysTime():
    now = datetime.datetime.now()
    return now.strftime("%c")

def updateTestInfoObj(main_version_index):
    test_info_table.setLatestBuildNo(main_version_index, g_latest_build_index)
    test_info_table.setLastTestTime(getSysTime(),g_latest_build_index)

def backupLogInfo(log_info):
    log_backup_file = open(os.getcwd()+r'\log_backup.txt','r+')
    log_backup_file.write(log_info)
    log_backup_file.close()
    
def runScheduledTask(): 
    global log
    while True:
        global g_is_test_stats_today
        g_is_test_stats_today = False

        today=int(time.strftime("%w"))
        while not g_is_test_stats_today:
            has_run_rft_today = [False]
            for item in test_info_table.test_info_list:
                today=int(time.strftime("%w"))
                log=""
                if hasNewBuild(item[KEY_WORD_LIST[MAIN_VERSION_INDEX]]):
                    log_file = open(os.getcwd()+r'\log.txt','a+')
                    log+=("\n**************************\n")
                    log+=("Date: "+getSysTime()+'\n')
                    print(g_latest_build_index)
                    log+=("Build NO: "+g_latest_build_index+"\n")
                    log+=("Test Start...\n")
                    
                    if installNewBuild(item[KEY_WORD_LIST[MAIN_VERSION_INDEX]],has_run_rft_today):
                        g_is_test_stats_today = True
                        updateTestInfoObj(item[KEY_WORD_LIST[MAIN_VERSION_INDEX]])
                        test_info_table.updateTestInfoFile()
                        log+=("Update 'test_info'\n")
                        
                    log+=("\n**************************\n")
                    log_file.write(log)
                    backupLogInfo(log)
                    log_file.close()
                
                if has_run_rft_today[0] == True:
                    g_is_test_stats_today = True
                                                        
                if g_is_test_stats_today:
                    print("Complete a test today!")
                    subject="Stats Client "+'.'.join(g_latest_build_index.split('.')[0:-1])+" [VC9_64] ("+g_latest_build_index+")"
                    g_email_sender.sendEmail(g_latest_build_index,subject,"Complete test of "+g_latest_build_index+"today!",SUCCESS)
                    break

            print("Is complete a test today?",g_is_test_stats_today)
            time.sleep(ONE_MIN)
            
        while True:
            print("Now start to wait for another day!")
            cur_date = int(time.strftime("%w"))
            if cur_date != today:
                print("Date changed!")
                g_is_test_stats_today = False
                break
            time.sleep(ONE_HOUR)

def installStats(main_version_index):
    version_index = main_version_index.split('.')[0]
    stats = copy.deepcopy(STATS_MSI)
    stats[-1] = stats[-1].replace("{VINDX}", version_index,1)
    
    global log
    stats_msi_absolute_path = os.path.join(*(LOCAL_BUILD_SAVING_PATH+[g_latest_build_index]+stats))
    print(stats_msi_absolute_path)
    auth_code = test_info_table.getInstallCode(main_version_index)
    install_dir = os.path.join(*(INSTALL_DIR))
    if not os.path.isdir(install_dir):
        os.mkdir(install_dir)
    
    log+=("start to install Stats...\n") 
    os.system(MSI_EXE + " /i " + "\"" + stats_msi_absolute_path + "\"" + " /qn /norestart /L*v logfile.txt " + "INSTALLDIR="+ "\"" + install_dir + "\"" + " AUTHCODE=" + "\"" + auth_code + "\"")   
    exe_file = os.path.join(*(INSTALL_DIR+["stats.exe"]))
    if os.path.isfile(exe_file):
        print("Succeed installing Stats!")
        log+=("Complete the installation...\n")
        return True
    else:
        print("Fail to install Stats!")
        subject="Stats Client "+'.'.join(g_latest_build_index.split('.')[0:-1])+" [VC9_64] ("+g_latest_build_index+")"
        g_email_sender.sendEmail(g_latest_build_index,subject, "There is an unknown error resulting in the failure of installing Stats "+g_latest_build_index\
                                                              +". The installation files is put in "+stats_msi_absolute_path.split('.')[0:-1]\
                                                              +". Please make sure the installation package is complete.", FAIL)
        log+=("Fail to install Stats...\n")
        return False
      
def uninstallStats(recent_test_build_index):
    global log
    log+=("Start to uninstall an old version...\n")
    install_dir = os.path.join(*(INSTALL_DIR)) 
    #check whether current build is installed
    if not os.path.isdir(install_dir):
        log+=("No old build has been insatlled!\n")    
        return True
    
    #uninstall stats
    main_version_index = '.'.join(recent_test_build_index.split('.')[0:-1])
    uninstall_code = test_info_table.getUninstallCode(main_version_index)
    os.system(MSI_EXE + " /X{"+uninstall_code+"} /qn /norestart /L*v logfile.txt ALLUSERS=1 REMOVE=\"ALL\"")
    
    exe_file = os.path.join(*(INSTALL_DIR+["stats.exe"]))
    if os.path.isfile(exe_file):
        print("Fail to uninstall Stats!")
        log+=("Fail to uninstall Stats...!\n")
        subject="Stats Client "+'.'.join(g_latest_build_index.split('.')[0:-1])+" [VC9_64] ("+g_latest_build_index+")"
        g_email_sender.sendEmail(g_latest_build_index,subject,"Before test "+g_latest_build_index+", fail to uninstall an old version of Stats "\
                                 +recent_test_build_index\
                                 +". Please uninstall it manually to continue automation test for a new build.", FAIL)
        return False
    else:
        if os.path.isdir(install_dir):
            os.system(r"C:\Windows\System32\attrib -r "+ install_dir+"\*.* " + " /s /d")
            shutil.rmtree(install_dir, ignore_errors = True)
        print("Succeed uninstalling Stats!")
        log+=("Succeed uninstalling Stats...!\n")
        return True

def clearEnvironment():
    #create log_backup file
    if not os.path.isfile(os.getcwd()+r'\log_backup.txt'):
        log_backup_file = open(os.getcwd()+r'\log_backup.txt','w+')
        log_backup_file.close()
    
    #clear log file and start current test 
    log_file = open(os.getcwd()+r'\log.txt','w+')    
    log_file.write("**********************************\n")
    log_file.write("*A new cycle of test is starting.*\n")
    log_file.write("*Beginning Data:" +getSysTime()+"*\n")
    log_file.write("**********************************\n")
    log_file.close()
    
    #when initiating this script, all Stats installed on the machine will be uninstalled first
    uninstall_code_dict = test_info_table.getUninstallCodeTable()
    for item in uninstall_code_dict.keys():
        os.system(MSI_EXE + " /X{"+uninstall_code_dict[item]+"} /qn /norestart /L*v logfile.txt ALLUSERS=1 REMOVE=\"ALL\"")
    
    #delete all remaining files and dirs generated by uninstalled Stats      
    install_dir = os.path.join(*INSTALL_DIR[0:2])
    if os.path.isdir(install_dir):
        os.system(r"C:\Windows\System32\attrib -r "+ install_dir+"\*.* " + " /s /d")
        shutil.rmtree(install_dir)
    os.mkdir(install_dir)
    
    #delete all the saving builds on the machine
    local_download_dir = os.path.join(*LOCAL_BUILD_SAVING_PATH)
    if os.path.isdir(local_download_dir):
        os.system(r"C:\Windows\System32\attrib -r "+ local_download_dir+"\*.* " + " /s /d")
        shutil.rmtree(local_download_dir)
    os.mkdir(local_download_dir)

    print("Complete clearing...")

if __name__ == '__main__':
    #including last successful test build in every main version
    global test_info_table
    test_info_table = TestInfo()
    
    #last test build
    global g_latest_build_index
     
    #dir of BVT report summary   
    global g_absolute_report_dir
     
    #dir of new build
    global g_absolute_build_dir
     
    #log file to record test process
    global log
    
    #send instant email
    global g_email_sender
    g_email_sender = SendEmail()

    clearEnvironment()
    runScheduledTask()