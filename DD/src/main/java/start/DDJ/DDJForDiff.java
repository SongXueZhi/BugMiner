package start.DDJ;

import org.apache.commons.io.FileUtils;
import start.*;

import java.io.File;
import java.io.IOException;


/**
 * @author lsn
 * @date 2023/4/3 2:53 PM
 */
public class DDJForDiff {

    static Executor executor = new Executor();
    private File projectDir;
    private Regression regression;
    private String tool;
    private String version;
    private boolean isDecomposed;
    private String projectName;
    private String message;
    private final int timeout = 7200;

    public DDJForDiff(File cacheDir, Regression regression, String tool, String version, boolean isDecomposed, String projectName) {
        this.regression = regression;
        this.tool = tool;
        this.version = version;
        this.isDecomposed = isDecomposed;
        this.projectName = projectName;
        this.message = version + "_ddj_" + tool + (isDecomposed ? "" : "_nodecomposed");
        this.projectDir = new File(cacheDir, message + File.separator + projectName);
    }

    public void checkout() throws IOException, InterruptedException {
        if (projectDir.exists() && !projectDir.isDirectory()) {
            projectDir.delete();
        }
        projectDir.mkdirs();
        executor.setDirectory(projectDir);

        Revision buggy = new Revision(regression.getBfc()+"~1","buggy");
        File buggyDir = new File(projectDir,regression.getId()+"_"+buggy.getName());
        if (buggyDir.exists()) {
            FileUtils.forceDelete(buggyDir);
        }
        String buggyCheckoutResult = executor.exec("defects4j checkout -p " + regression.getProject_full_name() + " -v "
                + regression.getId().replace(regression.getProject_full_name(), "") + "b -w " + regression.getId() + "_buggy");
        buggy.setLocalCodeDir(new File(projectDir, regression.getId() + "_buggy"));
        regression.setBuggyRev(buggy);

        Revision fix = new Revision(regression.getBfc(),"fix");
        File fixDir = new File(projectDir,regression.getId()+"_"+fix.getName());
        if (fixDir.exists()) {
            FileUtils.forceDelete(fixDir);
        }
        String fixCheckoutResult = executor.exec("defects4j checkout -p " + regression.getProject_full_name() + " -v "
                + regression.getId().replace(regression.getProject_full_name(), "") + "f -w " + regression.getId() + "_fix");
        fix.setLocalCodeDir(new File(projectDir, regression.getId() + "_fix"));
        regression.setBfcRev(fix);
        Thread.sleep(2000);
//        SourceManager.createShell(regression.getId(), message, projectName, fix, regression.getTestCaseString(), regression.getErrorType());
//        SourceManager.createShell(regression.getId(), message, projectName, buggy, regression.getTestCaseString(), regression.getErrorType());
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
        }else if(version.equals("defects4j") || version.equals("diff")) {
            godName = regressionID + "_fix";
            badName = regressionID + "_buggy";
        }
        System.out.println("start " +version + " ddj " + tool);
        if(isDecomposed){
            command = "timeout " + timeout + " ./cca_diff.py ddjava --include src/main/java --include src/java cache_projects" + File.separator + message + File.separator
                    + projectName.replace("/", "_") + " "
                    + godName +" "+ badName + " -a " + tool + " -d -v";
        }else {
            command = "timeout " + timeout + " ./cca_diff.py ddjava --include src/main/java --include src/java cache_projects" + File.separator + message + File.separator
                    + projectName.replace("/", "_") + " "
                    + godName + " " + badName + " -a " + tool + " --noresolve --noref --nochg";
        }
        System.out.println(command);
        executor.setDirectory(new File(Main.workSpacePath));
        executor.exec(command);

        SourceManager.getDiffResult(message, projectName , regressionID + "_" + message);
        SourceManager.cleanCache(message, projectName);
        SourceManager.backUP(message, projectName , regressionID);
    }

}
