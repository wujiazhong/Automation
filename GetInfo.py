#####################
import os,re,shutil
import time, datetime
from time import sleep

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

#6:00 am is test time for every day
CHECK_TIME = "06"

#Silent install arguments
MSI_EXE = r"C:\Windows\System32\msiexec.exe"
STATS_INSTALL_AUTH_CODE = {"23":"4a06043af421b746c5e7",
                           "24":"ff50159458f1d041d7e6"}
INSTALL_DIR = ["C:\\" ,"Statistics"] 
STATS_MSI = ["Windows","SPSSStatistics","win64","IBM SPSS Statistics 23.msi"]

#For US group, this is the Statistics nightly build schedule for now:
# 
#Sun         Mon        Tues       Wed        Thur       Fri        Sat  
#            23.0.0.1   23.0.1.0   23.0.0.1   23.0.1.0   24.0.0.0
#For our test, the program run test one day later:
VERSION_NO_LIST = {"23.0.0.1":[2,4],
                   "23.0.1.0":[3,5],
                   "24.0.0.0":[6]}
REST_DAYS = [1,7]

#Time
ONE_HOUR = 3600
HALF_HOUR = 1800
STATS_UNINSTALL_AUTH_CODE = {"23":"C3BA73A4-2A45-4036-8541-4F5F8146078B",
                             "24":"To Do"}

def getNewestVersionIndex(version_for_test, path):
    version_dir_list = list()
    for item in os.listdir(path):
        #match version 23.*.*.*.**
        if re.match("(^"+version_for_test+"\.\d{1,3}$)", item):
            version_dir_list.append(item)
    
    try:   
        if(len(version_dir_list) == 0):
            raise Exception
    except Exception:
        print(ERROR_MSG_NO_REQUIRED_VERSION)  
        exit(0)      
    
    #find newest version
    newest_version = version_dir_list[0]
    for item in version_dir_list:
        if int(item.split('.')[-1]) > int(newest_version.split('.')[-1]):
            newest_version = item
    return newest_version

def isPassTest(version_for_test):
    global g_version_index
    g_version_index = getNewestVersionIndex(version_for_test, os.path.join(*VERSION_DIRECTORY))
    
    global g_absolute_report_dir
    g_absolute_report_dir = os.path.join(*(VERSION_DIRECTORY+[g_version_index]+SUMMARY_DIRECTORY+[SUMMARY_FILE_NAME]))
    
    global g_absolute_build_dir
    g_absolute_build_dir= os.path.join(*(VERSION_DIRECTORY+[g_version_index]+BUILD_RELATIVE_DIR)) 
    
    if not os.path.isdir(g_absolute_build_dir):
        print("This newest build does not have Windows version!")
        return False

    try:
        fp = open(g_absolute_report_dir, 'r')
    except:
        print(ERROR_MSG_NO_FILE)
        return False
    
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
        #do something to notify guys that test has been passed 
        return True
    else:
        return False
        
def installNewBuild(version_for_test):
    if isPassTest(version_for_test):
        log.write("Identical rate is more than 80%, so BVT is OK...\n")
        des_dir = os.path.join(*(BUILD_DOWNLOAD_PATH+[g_version_index]))
        #os.chdir(des_dir)
        #need backup of build in destination directory??
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
        log.write("Start to uninstall an old version...\n")     
        uninstallStats() 
        log.write("Complete the uninstallation...\n")        
        print("Uninstall Stats successfully!")
        #install new version
        log.write("Start to install a new version...\n")
        installStats()
        log.write("Complete installation...\n")
        print("Install Stats successfully!")
        
        log.close() 
        return True       
        
    else:
        #do something to notify QA that test has not been passed 
        #send email to notify that the test failed  
        #TO DO
        log.write("The installation failed for the identical_rate is too low!\n")
        log.close() 
        return False

def getVersionNeedtest(week_date):
    for item in VERSION_NO_LIST.items():
        if week_date in item[1]:
            return item[0]
            
    
def runScheduledTask():   
    while True:
        now = datetime.datetime.now()
        today=int(time.strftime("%w"))
        cur_time = now.strftime("%H")
        
        if today in REST_DAYS or cur_time != CHECK_TIME:
            sleep(HALF_HOUR) 
            continue             
        else:
            #version_for_test = getVersionNeedtest(today)
            version_for_test = "23.0.0.1"
            
            global log 
            log = open(os.getcwd()+r'\log.txt','a+')
            log.write("**************************\n")
            log.write("Date: "+now.strftime("%c")+'\n')
            log.write("Test Start...\n")
            
            if installNewBuild(version_for_test):
                while True:
                    sleep(ONE_HOUR)
                    cur_date = int(time.strftime("%w"))
                    if cur_date != today:
                        break;
                continue
            else:
                print("Fail")
                break
    return

def getUninstallCode():
    if re.match("^23(\.\d{1,3}){4}$",g_version_index):
        return STATS_UNINSTALL_AUTH_CODE["23"]
    if re.match("^24(\.\d{1,3}){4}$",g_version_index):
        return STATS_UNINSTALL_AUTH_CODE["24"]

def installStats():
    stats_msi_absolute_path = os.path.join(*(BUILD_DOWNLOAD_PATH+[g_version_index]+STATS_MSI))
    auth_code = STATS_INSTALL_AUTH_CODE[g_version_index.split(".")[0]]
    install_dir = os.path.join(*(INSTALL_DIR+[g_version_index]))
    if not os.path.isdir(install_dir):
        os.mkdir(install_dir)
    
    os.system(MSI_EXE + " /i " + "\"" + stats_msi_absolute_path + "\"" + " /qn /norestart /L*v logfile.txt " + "INSTALLDIR="+ "\"" + install_dir + "\"" + " AUTHCODE=" + auth_code)
    
def uninstallStats():
    uninstall_code = getUninstallCode()
    os.system(MSI_EXE + r" /X{"+uninstall_code+"} /qn /norestart /L*v logfile.txt ALLUSERS=1 REMOVE='ALL'")
    
if __name__ == '__main__':  
    runScheduledTask()
