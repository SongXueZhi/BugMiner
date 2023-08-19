package start.DDJ;


import start.*;

import java.io.File;
import java.util.Arrays;
import java.util.List;

/**
 * @author lsn
 * @date 2023/3/9 8:15 PM
 */
public class DDJ {
    static Reducer reducer = new Reducer();
    static Migrator migrator = new Migrator();
    static Executor executor = new Executor();
    private File projectDir;
    private Regression regression;
    private String tool;
    private String version;
    private boolean isDecomposed;
    private String projectName;
    private String message;
    private final int timeout = 7200;

    public DDJ(File projectDir, Regression regression, String tool, String version, boolean isDecomposed, String projectName) {
        this.projectDir = projectDir;
        this.regression = regression;
        this.tool = tool;
        this.version = version;
        this.isDecomposed = isDecomposed;
        this.projectName = projectName;
        this.message = version + "_ddj_" + tool + (isDecomposed ? "" : "_nodecomposed");

    }

    public void checkout(){

        Revision bfc = new Revision(regression.getBfc(),"bfc");
        bfc.setLocalCodeDir(SourceManager.checkout(regression.getId(), bfc, projectDir, message, projectName));
        regression.setBfcRev(bfc);

        Revision buggy = new Revision(regression.getBfc()+"~1","buggy");
        buggy.setLocalCodeDir(SourceManager.checkout(regression.getId(),buggy, projectDir, message,projectName));
        regression.setBuggyRev(buggy);

        Revision bic = new Revision(regression.getBic(),"bic");
        bic.setLocalCodeDir(SourceManager.checkout(regression.getId(),bic, projectDir, message,projectName));
        regression.setBicRev(bic);

        Revision work = new Revision(regression.getWork(),"work");
        work.setLocalCodeDir(SourceManager.checkout(regression.getId(),work, projectDir, message,projectName));
        regression.setWorkRev(work);

        //步骤2 迁移测试用例
        List<Revision> needToTestMigrateRevisionList = Arrays.asList(new Revision[]{buggy, bic, work});
        migrateTestAndDependency(bfc, needToTestMigrateRevisionList, regression.getTestCaseString());

        SourceManager.createShell(regression.getId(), message, projectName, bic, regression.getTestCaseString());
        SourceManager.createShell(regression.getId(), message, projectName, work, regression.getTestCaseString());
        SourceManager.createShell(regression.getId(), message, projectName, bfc, regression.getTestCaseString());
        SourceManager.createShell(regression.getId(), message, projectName, buggy, regression.getTestCaseString());
    }


    public void runCCA() throws Exception {
        String projectName = projectDir.getName();
        String godName = "";
        String badName = "";
        String command;
        String regressionID = regression.getId();
        if(version.equals("bic")){
            godName = regressionID + "_bic";
            badName = regressionID + "_work";
        }else if(version.equals("bfc")){
            godName = regressionID + "_bfc";
            badName = regressionID + "_buggy";
        }
        if(isDecomposed){
            command = "timeout " + timeout + " ./cca.py ddjava --include src/main/java cache_projects" + File.separator + message + File.separator
                    + projectName.replace("/", "_") + " "
                    + godName +" "+ badName + " -a " + (tool.substring(0,5));
        }else {
            command = "timeout " + timeout + " ./cca.py ddjava --include src/main/java cache_projects" + File.separator + message + File.separator
                    + projectName.replace("/", "_") + " "
                    + godName + " " + badName + " -a " + (tool.substring(0,5)) + " --noresolve --noref --nochg";
        }
        System.out.println(command);
        executor.setDirectory(new File(Main.workSpacePath));
        executor.exec(command);

        SourceManager.getDDJResult(message, projectName , regressionID + "_" + message);
        SourceManager.cleanCache(message, projectName);
        SourceManager.backUP(message, projectName , regressionID);
    }


    static void migrateTestAndDependency(Revision rfc, List<Revision> needToTestMigrateRevisionList,
                                         String testCaseString) {
        migrator.equipRfcWithChangeInfo(rfc);
        reducer.reduceTestCases(rfc, testCaseString);
        needToTestMigrateRevisionList.forEach(revision -> {
            migrator.migrateTestFromTo_0(rfc, revision);
        });
    }

}
