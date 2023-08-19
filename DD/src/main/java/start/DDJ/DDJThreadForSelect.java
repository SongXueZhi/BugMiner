package start.DDJ;

import start.MysqlManager;
import start.Regression;
import start.SourceManager;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/**
 * @author lsn
 * @date 2023/7/11 3:27 PM
 */
public class DDJThreadForSelect {
    private String tool;
    private String version;
    private boolean isDecomposed;
    private String model;
    private int startId;
    private int endId;


    public DDJThreadForSelect(String tool, String version, boolean isDecomposed, String model) {
        this.tool = tool;
        this.version = version;
        this.isDecomposed = isDecomposed;
        this.model = model;
    }

    public DDJThreadForSelect(String tool, String version, boolean isDecomposed, int startId, int endId, String model) {
        this.tool = tool;
        this.version = version;
        this.isDecomposed = isDecomposed;
        this.startId = startId;
        this.endId = endId;
        this.model = model;
    }

    public void run() {
        List<String> uuid = readListFromFile("id.txt");
        System.out.println("regression size: " + uuid.size() + " ： " + String.join(" ", uuid));

        for (int i = 0; i < uuid.size(); i++) {
            try {
                String sql = "select * from regressions_all where id = " + uuid.get(i);
                Regression regression  = MysqlManager.selectRegressionstoList(sql).get(0);
                String projectName = regression.getProject_full_name();
                System.out.println(regression.getId() + " " + projectName + " " + tool +  " " + version + " " + isDecomposed + " " + model);
                File projectDir = SourceManager.getProjectDir(projectName);
                DDJForNew ddj = new DDJForNew(projectDir, regression, tool, version, isDecomposed, projectName, model);
                ddj.checkout();
                ddj.runCCA();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }


    public static List<String> readListFromFile(String path) {
        List<String> result = new ArrayList<>();
        File file = new File(path);
        try {
            InputStream is = new FileInputStream(file);
            if (file.exists() && file.isFile()) {
                BufferedReader br = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8));
                String line = null;
                while ((line = br.readLine()) != null) {
                    result.add(line);
                }
                br.close();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return result;
    }

    public static void main(String[] args) {
        DDJThreadForSelect ddjThreadForSelect = new DDJThreadForSelect("reldd", "bic", true, "log+matrix");
        ddjThreadForSelect.run();
    }
}
