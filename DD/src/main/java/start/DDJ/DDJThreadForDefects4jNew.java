package start.DDJ;


import start.Executor;
import start.Regression;
import start.SourceManager;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * @author lsn
 * @date 2023/7/20 7:04 PM
 */
public class DDJThreadForDefects4jNew extends Thread {
    static Executor executor = new Executor();
    private String tool;
    private String version;
    private boolean isDecomposed;
    private String model;

    public DDJThreadForDefects4jNew(String tool, String version, boolean isDecomposed, String model) {
        this.tool = tool;
        this.version = version;
        this.isDecomposed = isDecomposed;
        this.model = model;

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
            System.out.println(regression.getId() + " " + projectName + " " + tool +  " " + version + " " + isDecomposed + " " + model);
            try {
                DDJForDefects4jNew ddj = new DDJForDefects4jNew(new File(SourceManager.cacheProjectsDirPath), regression, tool, version, isDecomposed, projectName, model);
                ddj.checkout();
                ddj.runCCA();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    //读取data目录下的文件名，得到已经运行的regressions
    public List<String> getRegressions(){
        List<String> uuid = new ArrayList<>();
        List<String> dataName = SourceManager.getDataName();
        for(String name : dataName){
            String[] split = name.split("_");
            if(split.length == (isDecomposed ? 5: 6) && split[1].equals(version) && split[3].substring(0,5).equals(tool.substring(0,5)) && split[split.length-1].equals(model)){
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
//            if(pid == null || pid.equals("") || pid.equals(" ") || pid.equals("Chart") || pid.equals("Closure") || pid.equals("Mockito") || pid.equals("Math") ){
//                continue;
//            }
            if(!pid.equals("Gson")){
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
