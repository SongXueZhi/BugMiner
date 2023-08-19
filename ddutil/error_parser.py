import subprocess
import re
import os

class Error_Parser():
    maven_err_regular = r"\[ERROR\] (.*\.java):(?:\[(\d+),(\d+)\])? (.+)"
    maven_type_regular = r"(\w+):\s*(.+)"
    maven_class_regular = r'^[a-z]+(\.[a-z][a-z0-9]*)*\.([A-Z][a-zA-Z0-9]*)$'
    maven_method_regular = "((?:interface|enum|method) [\w.$]+(?:<.*?>)?(?:\(.*?\))?)"
    
        
    def parse_errors(self,output):
        err_set = list()
        
        error_pattern = re.compile(self.maven_err_regular)
        type_pattern = re.compile(self.maven_type_regular)
        class_pattern = re.compile(self.maven_class_regular)
        method_pattern = re.compile(self.maven_method_regular)
        
        lines = output.split("\n")
        line_index = -1
        while (line_index < len(lines)-1 and len(lines)>0):
            line_index +=1
            line = lines[line_index]
            match = error_pattern.match(line)
            v={}
            o={}
            if match:
                file_path, line_number, column_number, error_message = match.groups()
                v['loc'] = file_path
                v['line'] = line_number
                v['column'] = column_number
                    
                # Initialize the variables
                o_type, o_name, o_loc = None, None, None
                if 'cannot find symbol' not in line:
                    try:
                        class_match = class_pattern.search(line)
                        method_match = method_pattern.search(line)
                        if method_match:
                            o_type, o_name, o_loc= method_match.group() 
                        elif class_match:
                            o_type='class'
                            o_name=class_match.group()                        
                            o_loc =class_match.group()
                    except:
                        print(f"err parser{line}")                                  
                # Go through the following lines until a new error is found or the end is reached
                else:
                    try:
                        for index in range(0,2):
                            line_index += 1               
                            type_match = type_pattern.search(lines[line_index].strip())
                            if type_match:
                                current_type, current_value = type_match.groups()
                                if current_type == "symbol":
                                    o_type = current_value.split()[0]
                                    o_name = current_value.split()[1]
                                elif current_type == "location":
                                    o_loc = current_value
                    except:
                          print(f"err parser{line}")                
                o['loc']=o_loc
                o['type']=o_type
                o['name']=o_name
                err_set.append((v, o))  
        
        err_set = [t for i, t in enumerate(err_set) if t not in err_set[:i]]
        
        return err_set 

