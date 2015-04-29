import os,re,shutil
import time, datetime
from time import sleep
from TestInfo import TestInfo
from TestInfo import KEY_WORD_LIST

#report summary path information
SUMMARY_FILE_NAME = "results_summary.txt"
VERSION_DIRECTORY = [r"\\svs1bo01","Stats","builds","outputs","statisticsmedia"]
SUMMARY_DIRECTORY = ["reports","VC9_64","client"]

#build directory information
BUILD_RELATIVE_DIR = ["Client","Statistics", "dvd_WinClient"]
BUILD_DOWNLOAD_PATH = ["C:\\" ,"test"]

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
STATS_INSTALL_AUTH_CODE = {"23":"4a06043af421b746c5e7",
                           "24":"ff50159458f1d041d7e6"}
INSTALL_DIR = ["C:\\" ,"Statistics"] 
STATS_MSI = ["Windows","SPSSStatistics","win64","IBM SPSS Statistics 23.msi"]

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

    if float(Identical_Info)>=PASS_THRESHOLD and float(Identical_Info)<=100.0:
        log.write("Identical rate is more than 80%, so BVT passed...\n")
        print("BVT passed")
        return True
    else:
        log.write("Identical rate is less than 80%, so BVT did not pass...\n")
        print("BVT did not pass")
        return False
        
def installNewBuild():
    if isPassTest():
        des_dir = os.path.join(*(BUILD_DOWNLOAD_PATH+[g_version_index]))
        if os.path.isdir(des_dir):
            os.system(r"C:\Windows\System32\attrib -r "+ des_dir+"\*.* " + " /s /d")
            log.write("Start to clear old download build...\n")
            shutil.rmtree(des_dir, ignore_errors = True)
            log.write("Complete clearing old download build...\n")
         
        #download new version 
        log.write("Start to download latest build...\n")            
        shutil.copytree(g_absolute_build_dir,des_dir)
        log.write("Complete downloading latest build...\n")
       
        #uninstall old version
        if not uninstallStats():
            return False       
        #install new version
        if not installStats():
            return False 
        
        return True       
        
    else:
        #TO DO
        log.write("The installation failed!\n")
        log.write("**************************\n\n")
        log.close() 
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
                
def hasNewBuild(version_for_test):
    path = os.path.join(*VERSION_DIRECTORY)
    version_dir_list = list()
    for item in os.listdir(path):
        #match version 23.*.*.*.**
        if re.match("(^"+version_for_test+"\.\d{1,3}$)", item):
            version_dir_list.append(item)
    
    last_test_build_no = test_info_table.getLatestBuildNo(version_for_test)        
    #find newest version
    version_dir_list = sortVersionList(version_dir_list)
    for item in version_dir_list:
        if int(item.split('.')[-1]) > int(last_test_build_no.split('.')[-1]):
            g_version_index = item
            g_absolute_report_dir = os.path.join(*(VERSION_DIRECTORY+[g_version_index]+SUMMARY_DIRECTORY+[SUMMARY_FILE_NAME]))  
            if os.path.isfile(g_absolute_report_dir):         
                g_absolute_build_dir= os.path.join(*(VERSION_DIRECTORY+[g_version_index]+BUILD_RELATIVE_DIR))
    
    if int(g_version_index.split('.')[-1])>int(last_test_build_no.split('.')[-1]):
        return True
                
    while int(newest_version.split('.')[-1]) > int(last_test_build_no.split('.')[-1]): 
        g_version_index = newest_version
        g_absolute_report_dir = os.path.join(*(VERSION_DIRECTORY+[g_version_index]+SUMMARY_DIRECTORY+[SUMMARY_FILE_NAME]))  
        if os.path.isfile(g_absolute_report_dir):         
            g_absolute_build_dir= os.path.join(*(VERSION_DIRECTORY+[g_version_index]+BUILD_RELATIVE_DIR))
        else:
            build = int(newest_version.split('.')[-1])
            newest_version = '.'.join(newest_version.split('.')[0:-1]+[str(build-1)])
        return True
    
    g_version_index = last_test_build_no
    return False
    
def runScheduledTask(): 
    while True:
        now = datetime.datetime.now()
        today=int(time.strftime("%w"))
        
        for item in test_info_table:
            if hasNewBuild(item[KEY_WORD_LIST[0]]):
                sleep(HALF_HOUR)
                #do something 
                log = open(os.getcwd()+r'\log.txt','a+')
                log.write("\n**************************\n")
                log.write("Date: "+now.strftime("%c")+'\n')
                log.write("Build NO: "+g_version_index+"\n")
                log.write("Test Start...\n")
                
                if installNewBuild():
                    test_info_table.setLatestBuildNo(item[KEY_WORD_LIST[0]], g_version_index)
                
                log.close()
        
        while True:
            sleep(ONE_HOUR)
            cur_date = int(time.strftime("%w"))
            if cur_date != today:
                continue
                
                
#         if today in REST_DAYS or cur_time != CHECK_TIME:
#             sleep(HALF_HOUR) 
#             continue             
#         else:
#             #version_for_test = getVersionNeedtest(today)
#             version_for_test = "23.0.0.1"
#             
#             global log 
#             log = open(os.getcwd()+r'\log.txt','a+')
#             log.write("\n**************************\n")
#             log.write("Date: "+now.strftime("%c")+'\n')
#             log.write("Test Start...\n")
#             
#             if installNewBuild(version_for_test):
#                 while True:
#                     sleep(ONE_HOUR)
#                     cur_date = int(time.strftime("%w"))
#                     if cur_date != today:
#                         break;
#                 continue
#             else:
#                 print("Fail")
#                 break
    return

def installStats():
    stats_msi_absolute_path = os.path.join(*(BUILD_DOWNLOAD_PATH+[g_version_index]+STATS_MSI))
    auth_code = test_info_table.getInstallCode(g_version_index)
    install_dir = os.path.join(*(INSTALL_DIR+[g_version_index]))
    if not os.path.isdir(install_dir):
        os.mkdir(install_dir)
    
    log.write("start to install Stats...\n") 
    os.system(MSI_EXE + " /i " + "\"" + stats_msi_absolute_path + "\"" + " /qn /norestart /L*v logfile.txt " + "INSTALLDIR="+ "\"" + install_dir + "\"" + " AUTHCODE=" + auth_code)   
    exe_file = os.path.join(*(INSTALL_DIR+[g_version_index]+["stats.exe"]))
    if os.path.isfile(exe_file):
        print("Succeed installing Stats!")
        log.write("Complete the uninstallation...\n")
        return True
    else:
        print("Fail to install Stats!")
        log.write("Fail to install Stats...\n")
        return False
      
def uninstallStats():
    log.write("Start to uninstall an old version...\n") 
    uninstall_code = test_info_table.getUninstallCode(g_version_index)
    os.system(MSI_EXE + r" /X{"+uninstall_code+"} /qn /norestart /L*v logfile.txt ALLUSERS=1 REMOVE='ALL'")

    install_dir = os.path.join(*(INSTALL_DIR+[g_version_index]))
    exe_file = os.path.join(*(INSTALL_DIR+[g_version_index]+["stats.exe"]))
    if os.path.isfile(exe_file):
        print("Fail to uninstall Stats!")
        log.write("Fail to uninstall Stats...!")
        return False
    else:
        if os.path.isdir(install_dir):
            os.system(r"C:\Windows\System32\attrib -r "+ install_dir+"\*.* " + " /s /d")
            shutil.rmtree(install_dir, ignore_errors = True)
        print("Succeed uninstalling Stats!")
        log.write("Succeed uninstalling Stats...!")
        return True

    
if __name__ == '__main__':
    global test_info_table
    global g_version_index   
    global g_absolute_report_dir
    global g_absolute_build_dir
    global log
    
    test_info_table = TestInfo()
    runScheduledTask()
