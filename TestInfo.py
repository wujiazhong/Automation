import re,os
# major: major version number, between 17 and 99
# minor: minor version number, between 0 and 99
# modify: modify version number, between 0 and 9
# fixpack: fixpack version number, between 0 and 9
# build number: the build number, greater than 0
# main_version_no = major.minor.modify.fixpack

#WARNING: KEY_WORD_LIST matched the text sequence in test_info, DO NOT change the keywords of them
KEY_WORD_LIST = ["Main_Version","Last_Test_Build","Build_Install_Code","Build_Uninstall_Code"]
INIT_FILENAME = "test_info"

BUILD_ITEM_HEAD = "<Build_Entry>"
BUILD_ITEM_TAIL = r"</Build_Entry>"

class TestInfo:
    def __init__(self):
        fp_config = open(INIT_FILENAME,'r')
        config_info = fp_config.read()
                 
        basic_build_info = re.findall(KEY_WORD_LIST[0]+"=(.+?)\n",config_info,re.S)
        last_test_build_number = re.findall(KEY_WORD_LIST[1]+"=(.+?)\n",config_info,re.S)
        install_code = re.findall(KEY_WORD_LIST[2]+"=(.+?)\n",config_info,re.S)
        uninstall_code = re.findall(KEY_WORD_LIST[3]+"=(.+?)\n",config_info,re.S)
        
        i=0
        #e.g. self.test_info_list:
        #[{'Build_Uninstall_Code': 'C3BA73A4-2A45-4036-8541-4F5F8146078B', 'Last_Test_Build': '23.0.0.1.25', 'Build_Install_Code': '4a06043af421b746c5e7', 'Version_NO': '23.0.0.1'}, 
        # {'Build_Uninstall_Code': 'C3BA73A4-2A45-4036-8541-4F5F8146078B', 'Last_Test_Build': '23.0.0.1.25', 'Build_Install_Code': '4a06043af421b746c5e7', 'Version_NO': '23.0.1.0'}]

        self.test_info_list = list()
        while i<len(basic_build_info): 
            value_list=[basic_build_info[i],last_test_build_number[i],install_code[i],uninstall_code[i]] 
            self.test_info_list.append(dict(zip(KEY_WORD_LIST,value_list)))
            i+=1
        
        print(self.test_info_list)
        fp_config.close()
    
    def getLatestBuildNo(self,main_version_no):
        for table_item in self.test_info_list:
            for item in table_item.items():
                if item[1] == main_version_no:
                    return table_item[KEY_WORD_LIST[1]]              
        return ""
    
    def setLatestBuildNo(self,main_version_no,latest_build_NO):
        for table_item in self.test_info_list:
            for item in table_item.items():
                if item[1] == main_version_no:
                    table_item[KEY_WORD_LIST[1]] = latest_build_NO
                    return
    
    def getInstallCode(self,build_NO):
        for table_item in self.test_info_list:
            for item in table_item.items():
                if item[1] == build_NO:
                    return table_item[KEY_WORD_LIST[2]]              
        return ""
    
    def getUninstallCode(self,build_NO):
        for table_item in self.test_info_list:
            for item in table_item.items():
                if item[1] == build_NO:
                    return table_item[KEY_WORD_LIST[3]]              
        return ""
    
    def setLatestBuildNoInTestInfoFile(self,main_version_no):
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
            
    
            