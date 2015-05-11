import re,os
# major: major version number, between 17 and 99
# minor: minor version number, between 0 and 99
# modify: modify version number, between 0 and 9
# fixpack: fixpack version number, between 0 and 9
# build number: the build number, greater than 0
# main_version_no = major.minor.modify.fixpack

#WARNING: KEY_WORD_LIST matched the text sequence in test_info, DO NOT change the keywords of them
MAIN_VERSION_INDEX = 0                #"Main_Version"
LAST_TEST_BUILD_INDEX = 1             #"Last_Test_Build"
LAST_TEST_TIME = 2                    #"Last_Test_Time"
BUILD_INSTALL_CODE = 3                #"Build_Install_Code"
BUILD_UNINSTALL_CODE = 4              #"Build_Uninstall_Code"

KEYWORD = 0
VALUE = 1

KEY_WORD_LIST = ["Main_Version","Last_Test_Build","Last_Test_Time","Build_Install_Code","Build_Uninstall_Code"]
INIT_FILENAME = "test_info"

BUILD_ITEM_HEAD = "<Build_Entry>"
BUILD_ITEM_TAIL = r"</Build_Entry>"
NO_STATS_INSTALLED = "NONE"

class TestInfo:
    def __init__(self):
        fp_config = open(INIT_FILENAME,'r')
        config_info = fp_config.read()
                 
        basic_build_info = re.findall(KEY_WORD_LIST[MAIN_VERSION_INDEX]+"=(.+?)\n",config_info,re.S)
        last_test_build_number = re.findall(KEY_WORD_LIST[LAST_TEST_BUILD_INDEX]+"=(.+?)\n",config_info,re.S)
        last_test_time = re.findall(KEY_WORD_LIST[LAST_TEST_TIME]+"=(.+?)\n",config_info,re.S)
        install_code = re.findall(KEY_WORD_LIST[BUILD_INSTALL_CODE]+"=(.+?)\n",config_info,re.S)
        uninstall_code = re.findall(KEY_WORD_LIST[BUILD_UNINSTALL_CODE]+"=(.+?)\n",config_info,re.S)
        
        i=0
        self.test_info_list = list()
        while i<len(basic_build_info): 
            value_list=[basic_build_info[i],last_test_build_number[i],last_test_time[i],install_code[i],uninstall_code[i]] 
            self.test_info_list.append(dict(zip(KEY_WORD_LIST,value_list)))
            i+=1
            
        self.recent_test_build_index = NO_STATS_INSTALLED
        fp_config.close()
    
    def getLatestBuildNo(self,main_version_index):
        for table_item in self.test_info_list:
            for item in table_item.items():
                if item[VALUE] == main_version_index:
                    return table_item[KEY_WORD_LIST[LAST_TEST_BUILD_INDEX]]              
        return ""
    
    def setLatestBuildNo(self,main_version_index,latest_build_NO):
        for table_item in self.test_info_list:
            for item in table_item.items():
                if item[VALUE] == main_version_index:
                    table_item[KEY_WORD_LIST[LAST_TEST_BUILD_INDEX]] = latest_build_NO
                    return
                
    def setLastTestTime(self,last_test_time,latest_build_index):
        for table_item in self.test_info_list:
            for item in table_item.items():
                if item[VALUE] == latest_build_index:
                    table_item[KEY_WORD_LIST[LAST_TEST_TIME]] = last_test_time
                    return
    
    def getInstallCode(self,main_version_index):
        for table_item in self.test_info_list:
            for item in table_item.items():
                if item[VALUE] == main_version_index:
                    return table_item[KEY_WORD_LIST[BUILD_INSTALL_CODE]]              
        return ""
    
    def getUninstallCode(self,main_version_index):
        for table_item in self.test_info_list:
            for item in table_item.items():
                if item[VALUE] == main_version_index:
                    return table_item[KEY_WORD_LIST[BUILD_UNINSTALL_CODE]]              
        return ""
    
    def updateTestInfoFile(self):
        #self.setLatestBuildNo("23.0.0.1","23.0.0.1.44")       
        temp_file = INIT_FILENAME+'_temp' 
        fp_config_temp = open(temp_file,'w')
        
        
        for item in self.test_info_list:
            fp_config_temp.write(BUILD_ITEM_HEAD+"\n")
            for key in KEY_WORD_LIST:
                fp_config_temp.write(key+'=')
                fp_config_temp.write(item[key]+'\n')
            fp_config_temp.write(BUILD_ITEM_TAIL+"\n")

        fp_config_temp.close()
        os.remove(INIT_FILENAME)
        os.rename(temp_file,INIT_FILENAME)

    def getUninstallCodeTable(self):
        uninstall_code_dict = {}
        for table_item in self.test_info_list:
            uninstall_code_dict[table_item[KEY_WORD_LIST[MAIN_VERSION_INDEX]]] = table_item[KEY_WORD_LIST[BUILD_UNINSTALL_CODE]]
        return uninstall_code_dict
        
    def getRecentTestBuildIndex(self):
        return self.recent_test_build_index
    
    def setRecentTestBuildIndex(self, build_index):
        self.recent_test_build_index =  build_index         