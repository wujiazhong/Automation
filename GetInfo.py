import os,re,shutil
import time, datetime
import copy

from time import sleep

from TestInfo import MAIN_VERSION_INDEX
from TestInfo import TestInfo
from TestInfo import KEY_WORD_LIST

#report summary path information
SUMMARY_FILE_NAME = "results_summary.txt"
VERSION_DIRECTORY = [r"\\svs1bo01","Stats","builds","outputs","statisticsmedia"]
SUMMARY_DIRECTORY = ["reports","VC9_64","client"]

#build directory information
BUILD_RELATIVE_DIR = ["Client","Statistics", "dvd_WinClient"]
LOCAL_BUILD_SAVING_PATH = ["C:\\" ,"test"]

#target keyword
IDENTICAL = "Identical"

#error msg
ERROR_MSG_LOGIN = "Fail to log in!"
ERROR_MSG_NO_FILE = "Fail to open the file. Please check if the file exists!"
ERROR_MSG_NO_REQUIRED_VERSION = "Please check the version directory. No matched version requested is found!"

#threshold
PASS_THRESHOLD = 0.8*100

#Silent install arguments
MSI_EXE = r"C:\Windows\System32\msiexec.exe"
INSTALL_DIR = ["C:\\" ,"Statistics"] 
STATS_MSI = ["Windows","SPSSStatistics","win64","IBM SPSS Statistics {VINDX}.msi"]

#Time
ONE_HOUR = 3600
HALF_HOUR = 1800
    
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
        fp.close()
        exit(0)
     
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
        return False
        
def installNewBuild(main_version_index):
    global log 
    if isPassTest():
        des_dir = os.path.join(*(LOCAL_BUILD_SAVING_PATH+[g_latest_build_index]))
            
        #download new version 
        log+=("Start to download latest build...\n")
        print("Start to download new build...")
        shutil.copytree(g_absolute_build_dir,des_dir)
        log+=("Complete downloading latest build...\n")
        print("Complete downloading...")
              
        #install new version
        if not installStats(main_version_index):
            return False 

        #conduct RFT 
        #pass the build_index as an argument
        
        if not uninstallStats(main_version_index):
            return False
        
        if os.path.isdir(des_dir):
            os.system(r"C:\Windows\System32\attrib -r "+ des_dir+"\*.* " + " /s /d")
            log+=("Start to delete old download build...\n")
            shutil.rmtree(des_dir, ignore_errors = True)
            log+=("Complete deleting old download build...\n")
        return True       
        
    else:
        #TO DO
        log+=("The installation failed since BVT test did not pass!\n")
        log+=("**************************\n\n")
        return False
    
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
        for item in test_info_table.test_info_list:
            log=""
            if hasNewBuild(item[KEY_WORD_LIST[MAIN_VERSION_INDEX]]):
                #sleep(HALF_HOUR)
                #do something 
                log_file = open(os.getcwd()+r'\log.txt','a+')
                log+=("\n**************************\n")
                log+=("Date: "+getSysTime()+'\n')
                print(g_latest_build_index)
                log+=("Build NO: "+g_latest_build_index+"\n")
                log+=("Test Start...\n")
                
                if installNewBuild(item[KEY_WORD_LIST[MAIN_VERSION_INDEX]]):
                    updateTestInfoObj(item[KEY_WORD_LIST[MAIN_VERSION_INDEX]])
                    test_info_table.updateTestInfoFile()
                    log+=("Update 'test_info'\n")
                
                log+=("\n**************************\n")
                log_file.write(log)
                backupLogInfo(log)
                log_file.close()
                print("\n\n")
        
        today=int(time.strftime("%w"))
        while True:
            sleep(ONE_HOUR)
            cur_date = int(time.strftime("%w"))
            print(cur_date)
            if cur_date != today:
                break

def installStats(main_version_index):
    version_index = main_version_index.split('.')[0]
    stats = copy.deepcopy(STATS_MSI)
    stats[-1] = stats[-1].replace("{VINDX}", version_index,1)
    print(len(stats))
    print(stats)
    
    global log
    stats_msi_absolute_path = os.path.join(*(LOCAL_BUILD_SAVING_PATH+[g_latest_build_index]+stats))
    print(stats_msi_absolute_path)
    auth_code = test_info_table.getInstallCode(main_version_index)
    install_dir = os.path.join(*(INSTALL_DIR+[g_latest_build_index]))
    if not os.path.isdir(install_dir):
        os.mkdir(install_dir)
    
    log+=("start to install Stats...\n") 
    os.system(MSI_EXE + " /i " + "\"" + stats_msi_absolute_path + "\"" + " /qn /norestart /L*v logfile.txt " + "INSTALLDIR="+ "\"" + install_dir + "\"" + " AUTHCODE=" + auth_code)   
    exe_file = os.path.join(*(INSTALL_DIR+[g_latest_build_index]+["stats.exe"]))
    if os.path.isfile(exe_file):
        print("Succeed installing Stats!")
        log+=("Complete the installation...\n")
        return True
    else:
        print("Fail to install Stats!")
        log+=("Fail to install Stats...\n")
        return False
      
def uninstallStats(main_version_index):
    global log
    log+=("Start to uninstall an old version...\n")
    install_dir = os.path.join(*(INSTALL_DIR+[g_latest_build_index])) 
    if not os.path.isdir(install_dir):
        log+=("No current build has been insatlled!\n")    
        return True
    
    uninstall_code = test_info_table.getUninstallCode(main_version_index)
    os.system(MSI_EXE + " /X{"+uninstall_code+"} /qn /norestart /L*v logfile.txt ALLUSERS=1 REMOVE=\"ALL\"")
    
    install_dir = os.path.join(*(INSTALL_DIR+[g_latest_build_index]))
    exe_file = os.path.join(*(INSTALL_DIR+[g_latest_build_index]+["stats.exe"]))
    if os.path.isfile(exe_file):
        print("Fail to uninstall Stats!\n")
        log+=("Fail to uninstall Stats...!\n")
        return False
    else:
        if os.path.isdir(install_dir):
            os.system(r"C:\Windows\System32\attrib -r "+ install_dir+"\*.* " + " /s /d")
            shutil.rmtree(install_dir, ignore_errors = True)
        print("Succeed uninstalling Stats!\n")
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
    install_dir = os.path.join(*INSTALL_DIR)
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

    clearEnvironment()
    runScheduledTask()
