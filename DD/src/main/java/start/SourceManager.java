package start;

import org.apache.commons.io.FileUtils;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * @Author: sxz
 * @Date: 2022/12/26/20:32
 * @Description:
 */
public class SourceManager {
    public final static String metaProjectsDirPath = Main.workSpacePath + File.separator + "meta_projects";
    public final static String cacheProjectsDirPath = Main.workSpacePath + File.separator+ "cache_projects";
    public final static String saveDataPath = Main.workSpacePath+ File.separator+ "data";
    public final static String defects4jDiffPath = Main.workSpacePath+ File.separator+ "diff";

    public static File checkout(String regressionID,Revision revision, File projectFile, String message, String projectFullName) {
        //copy source code from meta project dir
        String projectDirName = projectFullName.replace("/", "_");
        File projectCacheDir = new File(cacheProjectsDirPath + File.separator + message + File.separator, projectDirName);
        if (projectCacheDir.exists() && !projectCacheDir.isDirectory()) {
            projectCacheDir.delete();
        }
        projectCacheDir.mkdirs();

        File revisionDir = new File(projectCacheDir,regressionID+"_"+revision.getName());
        try {
            if (revisionDir.exists()) {
                FileUtils.forceDelete(revisionDir);
            }
            FileUtils.copyDirectoryToDirectory(projectFile, projectCacheDir);
        } catch (IOException e) {
            System.out.println(e.getMessage());
            return null;
        }
        new File(projectCacheDir, projectDirName).renameTo(revisionDir);
        //git checkout
        if (GitUtils.checkout(revision.getCommitID(), revisionDir)) {
            return revisionDir;
        }
        return null;
    }

    public static File checkout(String regressionID,Revision revision, File projectFile, String projectFullName) {
        //copy source code from meta project dir
        String projectDirName = projectFullName.replace("/", "_");
        File projectCacheDir = new File(cacheProjectsDirPath + File.separator , projectDirName);
        if (projectCacheDir.exists() && !projectCacheDir.isDirectory()) {
            projectCacheDir.delete();
        }
        projectCacheDir.mkdirs();

        File revisionDir = new File(projectCacheDir,regressionID+"_"+revision.getName());
        try {
            if (revisionDir.exists()) {
                FileUtils.forceDelete(revisionDir);
            }
            FileUtils.copyDirectoryToDirectory(projectFile, projectCacheDir);
        } catch (IOException e) {
            System.out.println(e.getMessage());
            return null;
        }
        new File(projectCacheDir, projectDirName).renameTo(revisionDir);
        //git checkout
        if (GitUtils.checkout(revision.getCommitID(), revisionDir)) {
            return revisionDir;
        }
        return null;
    }

    //download source project
    public static File getProjectDir(String projectDirName) {
        String projectFullName = projectDirName.replace("_", "/");
        checkRequiredDir();
        File projectFile = new File(metaProjectsDirPath + File.separator + projectDirName);
        File[] child = projectFile.listFiles();
        if (projectFile.exists() && child != null && child.length != 0) {
            return projectFile;
        } else {
            try {
                GitUtils.clone(projectFile, "https://github.com/" + projectFullName + ".git");
                return projectFile;
            } catch (Exception exception) {
                System.out.println(exception.getMessage());
            }
        }
        return null;
    }

    private static void checkRequiredDir() {
        File metaProjectsDir = new File(metaProjectsDirPath);

        if (metaProjectsDir.exists()) {
            if (!metaProjectsDir.isDirectory()) {
                metaProjectsDir.delete();
                metaProjectsDir.mkdirs();
            }
        } else {
            metaProjectsDir.mkdirs();
        }

        File cacheProjectsDir = new File(cacheProjectsDirPath);
        if (cacheProjectsDir.exists()) {
            if (!cacheProjectsDir.isDirectory()) {
                cacheProjectsDir.delete();
                cacheProjectsDir.mkdirs();
            }
        } else {
            cacheProjectsDir.mkdirs();
        }
    }

    public static void saveData(File file, String newName) throws Exception{
        FileUtils.copyFile(file,new File(saveDataPath + File.separator + newName));
    }

    public static void getDDJResult(String message, String projectName, String newName) throws Exception{
        File projectDir = new File(cacheProjectsDirPath + File.separator + message + File.separator + projectName);
        String result = "";
        File[] child = projectDir.listFiles();
        for (File file : child) {
            if (file.getName().contains("__CCA__")) {
                File logFile = null;
                if(message.contains("reldd")){
                    logFile = new File(file, "data.log");
                }else {
                    logFile = new File(file, "data_old.log");
                }
                if (logFile.exists()) {
                    System.out.println("ddj result file :" + logFile);
                    SourceManager.saveData(logFile, newName);
                }
            }
        }
    }

    public static void saveDiff(File file, String newName) throws Exception{
        FileUtils.copyFile(file,new File(defects4jDiffPath + File.separator + newName));
    }

    public static void getDiffResult(String message, String projectName, String newName) throws Exception{
        File projectDir = new File(cacheProjectsDirPath + File.separator + message + File.separator + projectName);
        String result = "";
        File[] child = projectDir.listFiles();
        for (File file : child) {
            if (file.getName().contains("__CCA__")) {
                File logFile = new File(file, "data.log");
                if (logFile.exists()) {
                    System.out.println("ddj result file :" + logFile);
                    SourceManager.saveDiff(logFile, newName);
                }
            }
        }
    }

    public static void createShell(String regressionID, String projectFullName, Revision revision, String testcase,
                            String errorType) {
        String projectDirName = projectFullName.replace("/", "_");
        File buildFile =
                new File(cacheProjectsDirPath + File.separator + projectDirName + File.separator + regressionID+"_"+revision.getName(),
                        "build.sh");
        File testFile =
                new File(cacheProjectsDirPath + File.separator + projectDirName + File.separator +  regressionID+"_"+revision.getName(),
                        "test.sh");
        if (!buildFile.exists()) {
            try {
                buildFile.createNewFile();
                String s1 = "#!/bin/bash";
                String s2 = "mvn clean compile test-compile &> /dev/null";
                FileUtils.write(buildFile, s1 + "\n" + s2, "UTF-8");
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        if (!testFile.exists()) {
            try {
                testFile.createNewFile();
                String s1 = "#!/bin/bash" + "\n";
                String s2 = "_OUT=$(timeout 300 mvn test -Dtest=" + testcase + " 2>&1)" + "\n";
                String s3 = "SUCCESS=$(echo ${_OUT} | grep -c 'BUILD SUCCESS')" + "\n";
                String s4 = "FAIL=$(echo ${_OUT} | grep -c '" + errorType + "')" + "\n";
                String s5 = "if\n" +
                        " [ \"${SUCCESS}\" = '1' ]; then\n" +
                        "    PASS='1'\n" +
                        "else\n" +
                        "    PASS='0'\n" +
                        "fi\n" +
                        "\n" +
                        "if [ ${PASS} = '1' -a ${FAIL} = '0' ]; then\n" +
                        "    /bin/echo -n 'PASS'\n" +
                        "elif [ ${FAIL} = '1' ]; then\n" +
                        "    /bin/echo -n 'FAIL'\n" +
                        "else\n" +
                        "    /bin/echo -n 'UNRESOLVED'\n" +
                        "fi";
                FileUtils.write(testFile, s1 + s2 + s3 + s4 + s5, "UTF-8");
            } catch (IOException e) {
                e.printStackTrace();
            }

        }
        buildFile.setExecutable(true,false);
        buildFile.setReadable(true,false);
        buildFile.setWritable(true,false);
        testFile.setExecutable(true,false);
        testFile.setReadable(true,false);
        testFile.setWritable(true,false);
    }

    public static void createShellForBugBuilder(String regressionID, String message, String projectFullName, Revision revision, String testcase) {
        String projectDirName = projectFullName.replace("/", "_");
        File buildFile =
                new File(cacheProjectsDirPath + File.separator + message + File.separator + projectDirName + File.separator + regressionID+"_"+revision.getName(),
                        "build.sh");
        File testFile =
                new File(cacheProjectsDirPath + File.separator + message + File.separator + projectDirName + File.separator +  regressionID+"_"+revision.getName(),
                        "test.sh");
        if (!buildFile.exists()) {
            try {
                buildFile.createNewFile();
                buildFile.canRead();
                buildFile.canExecute();
                buildFile.canWrite();
                String s1 = "#!/bin/bash";
                String s2 = "mvn clean compile test-compile";
                FileUtils.write(buildFile, s1 + "\n" + s2, "UTF-8");
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        if (!testFile.exists()) {
            try {
                testFile.createNewFile();
                buildFile.canRead();
                buildFile.canExecute();
                buildFile.canWrite();
                String s1 = "#!/bin/bash" + "\n";
                String s2 = "timeout 300 mvn test -Dtest=" + testcase  + "\n";
                FileUtils.write(testFile, s1 + s2 , "UTF-8");
            } catch (IOException e) {
                e.printStackTrace();
            }

        }
        buildFile.setExecutable(true,false);
        buildFile.setReadable(true,false);
        buildFile.setWritable(true,false);
        testFile.setExecutable(true,false);
        testFile.setReadable(true,false);
        testFile.setWritable(true,false);
    }

    public static void createShellForNew(String regressionID,String message, String projectFullName, Revision revision, String testcase) {
        String projectDirName = projectFullName.replace("/", "_");
        File buildFile =
                new File(cacheProjectsDirPath + File.separator + message + File.separator + projectDirName + File.separator + regressionID+"_"+revision.getName(),
                        "build.sh");
        File testFile =
                new File(cacheProjectsDirPath + File.separator + message + File.separator + projectDirName + File.separator +  regressionID+"_"+revision.getName(),
                        "test.sh");
        if (!buildFile.exists()) {
            try {
                buildFile.createNewFile();
                buildFile.canRead();
                buildFile.canExecute();
                buildFile.canWrite();
                String s1 = "#!/bin/bash";
                String s2 = "mvn clean compile test-compile -Dstyle.color=never -q";
                FileUtils.write(buildFile, s1 + "\n" + s2, "UTF-8");
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        if (!testFile.exists()) {
            try {
                testFile.createNewFile();
                String s1 = "#!/bin/bash" + "\n";
                String s2 = "_OUT=$(timeout 300 mvn test -Dtest=" + testcase + " 2>&1)" + "\n";
                String s3 = "SUCCESS=$(echo ${_OUT} | grep -c 'BUILD SUCCESS')" + "\n";
                String s4 = "CE=$(echo ${_OUT} | grep -c 'COMPILATION ERROR')" + "\n";
                String s5 = "if\n" +
                        " [ \"${SUCCESS}\" = '1' ]; then\n" +
                        "    PASS='1'\n" +
                        "else\n" +
                        "    PASS='0'\n" +
                        "fi\n" +
                        "\n" +
                        "if [ ${PASS} = '1' -a ${CE} = '0' ]; then\n" +
                        "    /bin/echo -n 'PASS'\n" +
                        "elif [ ${CE} = '1' ]; then\n" +
                        "    /bin/echo -n 'CE'\n" +
                        "else\n" +
                        "    /bin/echo -n 'FAIL'\n" +
                        "fi";
                FileUtils.write(testFile, s1 + s2 + s3 + s4 + s5, "UTF-8");
            } catch (IOException e) {
                e.printStackTrace();
            }

        }
        buildFile.setExecutable(true,false);
        buildFile.setReadable(true,false);
        buildFile.setWritable(true,false);
        testFile.setExecutable(true,false);
        testFile.setReadable(true,false);
        testFile.setWritable(true,false);
    }

    public static void createShell(String regressionID, String message, String projectFullName, Revision revision, String testcase) {
        String projectDirName = projectFullName.replace("/", "_");
        File buildFile =
                new File(cacheProjectsDirPath + File.separator + message + File.separator + projectDirName + File.separator + regressionID+"_"+revision.getName(),
                        "build.sh");
        File testFile =
                new File(cacheProjectsDirPath + File.separator + message + File.separator + projectDirName + File.separator +  regressionID+"_"+revision.getName(),
                        "test.sh");
        if (!buildFile.exists()) {
            try {
                buildFile.createNewFile();
                buildFile.canRead();
                buildFile.canExecute();
                buildFile.canWrite();
                String s1 = "#!/bin/bash";
                String s2 = "mvn clean compile test-compile &> /dev/null";
                FileUtils.write(buildFile, s1 + "\n" + s2, "UTF-8");
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        if (!testFile.exists()) {
            try {
                testFile.createNewFile();
                String s1 = "#!/bin/bash" + "\n";
                String s2 = "_OUT=$(timeout 300 mvn test -Dtest=" + testcase + " 2>&1)" + "\n";
                String s3 = "SUCCESS=$(echo ${_OUT} | grep -c 'BUILD SUCCESS')" + "\n";
                String s4 = "CE=$(echo ${_OUT} | grep -c 'COMPILATION ERROR')" + "\n";
                String s5 = "if\n" +
                        " [ \"${SUCCESS}\" = '1' ]; then\n" +
                        "    PASS='1'\n" +
                        "else\n" +
                        "    PASS='0'\n" +
                        "fi\n" +
                        "\n" +
                        "if [ ${PASS} = '1' -a ${CE} = '0' ]; then\n" +
                        "    /bin/echo -n 'PASS'\n" +
                        "elif [ ${CE} = '1' ]; then\n" +
                        "    /bin/echo -n 'UNRESOLVED'\n" +
                        "else\n" +
                        "    /bin/echo -n 'FAIL'\n" +
                        "fi";
                FileUtils.write(testFile, s1 + s2 + s3 + s4 + s5, "UTF-8");
            } catch (IOException e) {
                e.printStackTrace();
            }

        }
        buildFile.setExecutable(true,false);
        buildFile.setReadable(true,false);
        buildFile.setWritable(true,false);
        testFile.setExecutable(true,false);
        testFile.setReadable(true,false);
        testFile.setWritable(true,false);
    }

    public static void createShell(String regressionID, String message, String projectFullName, Revision revision, String testcase, String errorType) {
        String projectDirName = projectFullName.replace("/", "_");
        File buildFile =
                new File(cacheProjectsDirPath + File.separator + message + File.separator + projectDirName + File.separator + regressionID+"_"+revision.getName(),
                        "build.sh");
        File testFile =
                new File(cacheProjectsDirPath + File.separator + message + File.separator + projectDirName + File.separator +  regressionID+"_"+revision.getName(),
                        "test.sh");
        if (!buildFile.exists()) {
            try {
                buildFile.createNewFile();
                buildFile.canRead();
                buildFile.canExecute();
                buildFile.canWrite();
                String s1 = "#!/bin/bash";
                String s2 = "defects4j compile &> /dev/null";
                FileUtils.write(buildFile, s1 + "\n" + s2, "UTF-8");
            } catch (IOException e) {
                System.out.println("create build.sh failed " + buildFile.getAbsolutePath() );
                e.printStackTrace();
            }
        }
        if (!testFile.exists()) {
            try {
                testFile.createNewFile();
                String s1 = "#!/bin/bash" + "\n";
                String s2 = "test_result=$(timeout 10m defects4j test -t " + testcase + " 2>&1)" + "\nfilename='failing_tests'\n";
                String s3 = "search_string='" + errorType + "'\n";
                String s4 = "if grep -q \"$search_string\" \"$filename\"; then" + "\n";
                String s5 = "   echo  -n 'FAIL'" + "\n";
                String s6 = "elif echo \"$test_result\" | grep -q 'Failing tests: 0'; then" + "\n";
                String s7 = "   echo  -n 'PASS'" + "\n";
                String s8 = "else" + "\n";
                String s9 = "   echo  -n 'UNRESOLVED'" + "\n";
                String s10 = "fi" + "\n";
                FileUtils.write(testFile, s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8 + s9 + s10, "UTF-8");
            } catch (IOException e) {
                System.out.println("create test.sh failed " + testFile.getAbsolutePath());
                e.printStackTrace();
            }

        }
        buildFile.setExecutable(true,false);
        buildFile.setReadable(true,false);
        buildFile.setWritable(true,false);
        testFile.setExecutable(true,false);
        testFile.setReadable(true,false);
        testFile.setWritable(true,false);
    }

    public static void cleanCache(String message, String projectName) throws Exception{
        File projectDir = new File(cacheProjectsDirPath + File.separator + message + File.separator + projectName);
        File[] child = projectDir.listFiles();
        for (File file : child) {
            if (!file.getName().contains("__CCA__")) {
                if(file.isDirectory()){
                    Executor executor = new Executor();
                    executor.exec("sudo rm -rf " + file.getAbsolutePath());
//                    FileUtils.deleteDirectory(file);
                }
            }
        }
    }

    public static void backUP(String message, String projectName, String regressionID) throws IOException {
        File projectDir = new File(cacheProjectsDirPath + File.separator + message + File.separator + projectName);
        File[] child = projectDir.listFiles();
        for (File file : child) {
            if (file.getName().contains("__CCA__")) {
                file.renameTo(new File(projectDir,regressionID + "_" + message));

            }
        }
    }

    //得到data目录下的所有文件名
    public static List<String> getDataName(){
        List<String> dataName = new ArrayList<>();
        File file = new File(saveDataPath);
        File[] files = file.listFiles();
        for (File f : files) {
            dataName.add(f.getName());
        }
        return dataName;
    }

    public static List<String> getDefects4jDiffName(){
        List<String> dataName = new ArrayList<>();
        File file = new File(defects4jDiffPath);
        File[] files = file.listFiles();
        for (File f : files) {
            dataName.add(f.getName());
        }
        return dataName;
    }
}
