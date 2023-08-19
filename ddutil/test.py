import re

error_messages = [
    "[Error] /path/src/main/java/com/cflint/plugins/exceptions/DefaultCFLintExceptionListener.java:[12,8] com.cflint.plugins.exceptions.DefaultCFLintExceptionListener is not abstract and does not override abstract method exceptionOccurred(java.lang.Exception,java.lang.String,java.lang.String,java.lang.Integer,java.lang.Integer,java.lang.String,java.lang.String) in com.cflint.plugins.exceptions.CFLintExceptionListener",
    "[Error] /path/src/main/java/com/cflint/CFLint.java:[275,37] variable elements is already defined in method process(java.lang.String,java.lang.String) [INFO] 1 error",
    "[Error] /root/data/miner_space/transfer_cache/123/e25558f7-dab7-4f42-9f0c-e20bcc54214c/bic/src/main/java/com/cflint/main/CFLintMain.java:[139,23] cannot access com.cflint.main.CFLintMain",
    "[Error] /path/src/main/java/com/cflint/CFLint.java:[272,17] cannot find symbol\n[Error] symbol:   class ParserTag\n[Error] location: class com.cflint.CFLint"
]

def extract_vo(error_message):
    v_pattern = r"\[Error\](.*\.java):(?:\[(\d+),(\d+)\])"
    o_pattern = r"((?:class|interface|enum|method) [\w.$]+(?:<.*?>)?(?:\(.*?\))?)"
    
    v_match = re.search(v_pattern, error_message)
    o_match = re.search(o_pattern, error_message)
    
    if v_match:
        v = {
            'loc': v_match.group(1),
            'line': int(v_match.group(2)),
            'column': int(v_match.group(3))
        }
    else:
        v = None

    if o_match:
        o_type = o_match.group(1).split()[0]
        o_name = o_match.group(1).split()[1]
        o = {
            'loc': None,
            'type': o_type,
            'name': o_name
        }
    else:
        o = None

    return v, o

for error_message in error_messages:
    v, o = extract_vo(error_message)
    print(f"V: {v}, O: {o}\n")
