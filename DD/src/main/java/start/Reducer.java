package start;

import org.apache.commons.io.FileUtils;
import org.eclipse.jdt.core.dom.*;


import java.io.File;
import java.io.IOException;
import java.util.*;

public class Reducer {

    public void reduceTestCases(Revision revision, String testCase) {
        List<TestFile> testFiles = new ArrayList<>();
        String[] testCasesArray = testCase.split(";");
        Map<String,Set<String>> testFileMap = new HashMap<>();

        for (String testCaseS : testCasesArray){
            String[] testString = testCaseS.split("#");
            if (testString.length!=2){
                continue;
            }
          if(!testFileMap.containsKey(testString[0])){
              testFileMap.put(testString[0],new HashSet<>());
          }
          testFileMap.get(testString[0]).add(testString[1]);
        }

        for (ChangedFile changedFile : revision.getChangedFiles()){

            if (!(changedFile instanceof TestFile)){
                continue;
            }

            TestFile testFile = (TestFile) changedFile;
            String testKey = checkTestFile(changedFile.getNewPath(),testFileMap.keySet());
           if (testKey != null){
               testFile.testMethods.addAll(testFileMap.get(testKey));
           }
           testFiles.add(testFile);
        }
        purgeUnlessTestcase(testFiles, revision);
    }
    public String  checkTestFile(String newPath, Set<String> pattern){
        newPath = newPath.replace("/",".");
        for (String s : pattern){
            if (newPath.contains(s)){
                System.out.println(newPath+"+ is compare");
                return s;
            }
        }
        System.err.println(newPath+"+ is not compare");
        return null;
    }

    public void purgeUnlessTestcase(List<TestFile> testSuiteList, Revision bfc) {
        File bfcDir = bfc.getLocalCodeDir();
        for (TestFile testFile : testSuiteList) {
            String path = testFile.getNewPath();
            File file = new File(bfcDir, path);
            try {
                CompilationUnit unit = CodeUtil.parseCompliationUnit(FileUtils.readFileToString(file,
                        "UTF-8"));
                Set<String> testCaseSet = testFile.testMethods;
                List<TypeDeclaration> types = unit.types();
                for (TypeDeclaration type : types) {
                    MethodDeclaration[] mdArray = type.getMethods();
                    for (int i = 0; i < mdArray.length; i++) {
                        MethodDeclaration method = mdArray[i];
                        String name = method.getName().toString();

                        if ((method.toString().contains("@Test") || name.startsWith("test") || name.endsWith("test")) && !testCaseSet.contains(name)) {
                            method.delete();
                        }
                    }
                }
                List<ImportDeclaration> imports = unit.imports();
                int len = imports.size();
                ImportDeclaration[] importDeclarations = new ImportDeclaration[len];
                for (int i = 0; i < len; i++) {
                    importDeclarations[i] = imports.get(i);
                }

                for (ImportDeclaration importDeclaration : importDeclarations) {
                    String importName = importDeclaration.getName().getFullyQualifiedName();
                    if (importName.lastIndexOf(".") > -1) {
                        importName = importName.substring(importName.lastIndexOf(".") + 1);
                    } else {
                        importName = importName;
                    }

                    boolean flag = false;
                    for (TypeDeclaration type : types) {
                        if (type.toString().contains(importName)) {
                            flag = true;
                        }
                    }
                    if (!(flag || importDeclaration.toString().contains("*"))) {
                        importDeclaration.delete();
                    }
                }
                if (file.exists()){
                    file.delete();
                }
                FileUtils.writeStringToFile(file, unit.toString());
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }
}
