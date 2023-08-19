package start.DDJ;

import start.Executor;
import start.Regression;
import start.SourceManager;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * @author lsn
 * @date 2023/4/3 2:53 PM
 */
public class DDJThreadForDiff extends Thread{
    static Executor executor = new Executor();
    private String tool;
    private String version;
    private boolean isDecomposed;

    public DDJThreadForDiff(String tool, String version, boolean isDecomposed) {
        this.tool = tool;
        this.version = version;
        this.isDecomposed = isDecomposed;
    }

    public void run() {
        List<Regression> regressions  = getRegressionFromDefects4j();
        System.out.println("regression size: " + regressions.size());
        List<String> uuid = getRegressions();
        regressions.removeIf(regression -> uuid.contains(regression.getId()));
        System.out.println("run regression size: " + regressions.size());
        for (int i = 0; i < regressions.size(); i++) {
            Regression regression = regressions.get(i);
            String projectName = regression.getProject_full_name();
            System.out.println(projectName + " " + tool +  " " + version + " " + isDecomposed);
            System.out.println(regression.getId());
            try {
                DDJForDiff ddj = new DDJForDiff(new File(SourceManager.cacheProjectsDirPath), regression, tool, version, isDecomposed, projectName);
                ddj.checkout();
                ddj.runCCA();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    //读取defects4j_diff目录下的文件名，得到已经运行的regressions
    public List<String> getRegressions(){
        List<String> uuid = new ArrayList<>();
        List<String> dataName = SourceManager.getDefects4jDiffName();
        for(String name : dataName){
            String[] split = name.split("_");
            if(split.length == (isDecomposed ? 4: 5) && split[1].equals(version) && split[3].equals(tool)){
                uuid.add(split[0]);
            }
        }
        return uuid;
    }

    public List<Regression> getRegressionFromDefects4j(){
        String pidResult = executor.exec("defects4j pids");
        String[] pids = pidResult.split("\n");
        List<Regression> regressions = new ArrayList<>();
        for(String pid : pids){
            //todo 后续单独处理
            if(pid == null || pid.equals("") || pid.equals(" ") || pid.equals("Chart") || pid.equals("Closure") || pid.equals("Mockito")){
                continue;
            }
            String bidResult = executor.exec("defects4j bids -p " + pid);
            String[] bids = bidResult.split("\n");
            for (String bid : bids){
                if(bid == null || bid.equals("") || bid.equals(" ")){
                    continue;
                }
                String infoResult = executor.exec("defects4j info -p " + pid + " -b " + bid);
                Regression regression = new Regression();
                regression.setProject_full_name(pid);
                regression.setId(pid + bid);
                regression.setBfc(extractString(infoResult, "Revision ID \\(fixed version\\):\n", "\n"));
                regression.setTestCaseString(extractString(infoResult,
                        "Root cause in triggering tests:\n - ", "\n"));
                regression.setErrorType(extractString(infoResult, regression.getTestCaseString() + "\n   --> ", "\n"));
                regressions.add(regression);
            }
        }
        return regressions;

    }

    public static String extractString(String input, String start, String end) {
        String patternString = start + "([^\n]+)" + end;
        Pattern pattern = Pattern.compile(patternString);
        Matcher matcher = pattern.matcher(input);
        if (matcher.find()) {
            return matcher.group(1);
        } else {
            return null;
        }
    }

}
