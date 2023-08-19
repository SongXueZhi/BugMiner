package start.DDJ;


import start.MysqlManager;
import start.Regression;
import start.SourceManager;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

/**
 * @author lsn
 * @date 2023/3/22 10:46 AM
 */
public class DDJThread extends Thread {
    private String tool;
    private String version;
    private boolean isDecomposed;
    private int startId = 0;
    private int endId = 1800;

    public DDJThread( String tool, String version, boolean isDecomposed) {
        this.tool = tool;
        this.version = version;
        this.isDecomposed = isDecomposed;
    }

    public DDJThread( String tool, String version, boolean isDecomposed, int startId, int endId) {
        this.tool = tool;
        this.version = version;
        this.isDecomposed = isDecomposed;
        this.startId = startId;
        this.endId = endId;
    }
    public void run() {
        //String sql = "select * from regressions_all where id = 20";
        String sql = "select * from regressions_all where is_clean=1 and is_dirty=0 and id >= " + startId + " and id <= " + endId;
        List<Regression> regressions  = MysqlManager.selectRegressionstoList(sql);
        System.out.println("regression size: " + regressions.size());
        List<String> uuid = getRegressions();
        regressions.removeIf(regression -> uuid.contains(regression.getId()));
        System.out.println("run regression size: " + regressions.size());
        for (int i = 0; i < regressions.size(); i++) {
            Regression regression = regressions.get(i);
            String projectName = regression.getProject_full_name();
            System.out.println(projectName + " " + tool +  " " + version + " " + isDecomposed);
            File projectDir = SourceManager.getProjectDir(projectName);
            System.out.println(regression.getId());
            try {
                DDJ ddj = new DDJ(projectDir, regression, tool, version, isDecomposed, projectName);
                ddj.checkout();
                ddj.runCCA();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    //读取data目录下的文件名得到已经运行的regressions
    public List<String> getRegressions(){
        List<String> uuid = new ArrayList<>();
        List<String> dataName = SourceManager.getDataName();
        for(String name : dataName){
            String[] split = name.split("_");
            if(split.length == (isDecomposed ? 4: 5) && split[1].equals(version) && split[3].substring(0,5).equals(tool.substring(0,5))){
                uuid.add(split[0]);
            }
        }
        return uuid;
    }

}
