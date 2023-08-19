package start;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.sql.*;
import java.util.UUID;

/**
 * @author lsn
 * @date 2023/4/24 3:09 PM
 */
public class DataBaseTransfer {
    // 数据库连接参数
    static String sourceDbUrl = "jdbc:mysql://10.176.34.99:3306/regression?useSSL=false&allowPublicKeyRetrieval=true&characterEncoding=UTF8";
    static String sourceDbUsername = "root";
    static String sourceDbPassword = "110120";
    static String sourceTableName = "regressions_all";

    static String targetDbUrl = "jdbc:mysql://10.176.34.95:3306/code_annotation2?useSSL=false&allowPublicKeyRetrieval=true&characterEncoding=UTF8";
    static String targetDbUsername = "root";
    static String targetDbPassword = "1235";
    static String targetTableName = "regression";
    static String projectTableName = "project_name";

    public static void main(String[] args) {

        // 连接源数据库
        try (Connection sourceConn = DriverManager.getConnection(sourceDbUrl, sourceDbUsername, sourceDbPassword);
             Statement sourceStmt = sourceConn.createStatement();
             ResultSet sourceRs = sourceStmt.executeQuery("SELECT * FROM " + sourceTableName)) {

            // 连接目标数据库
            try (Connection targetConn = DriverManager.getConnection(targetDbUrl, targetDbUsername, targetDbPassword);
                 PreparedStatement targetStmt = targetConn.prepareStatement(
                         "INSERT IGNORE INTO " + targetTableName + " (id, regression_uuid, project_uuid, project_full_name, " +
                                 "bfc, buggy, bic, work, testcase) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")) {
                while (sourceRs.next()) {
                    // 从源数据库表中读取数据
                    int id = sourceRs.getInt("id");
                    String projectName = sourceRs.getString("project_name");
                    String bfc = sourceRs.getString("bfc");
                    String bic = sourceRs.getString("bic");
                    String wc = sourceRs.getString("wc");
                    String testcase1 = sourceRs.getString("testcase1");

                    // 插入处理后的数据到目标数据库表中
                    targetStmt.setInt(1, id);
                    targetStmt.setString(2, generateRegressionUUID());
                    targetStmt.setString(3, queryProjectUuid(targetConn, projectName.replace("_","/")));
                    targetStmt.setString(4, projectName.replace("_","/"));
                    targetStmt.setString(5, bfc);
                    targetStmt.setString(6, getPreviousCommitId(bfc, projectName));
                    targetStmt.setString(7, bic);
                    targetStmt.setString(8, wc);
                    targetStmt.setString(9, testcase1);
                    targetStmt.executeUpdate();
                }

                System.out.println("数据传输完成！");
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    public static String getPreviousCommitId(String commitId, String projectName){
        String command = "git rev-parse " + commitId + "^"; // Git命令
        Executor executor = new Executor();
        executor.setDirectory(new File("/Users/lsn/ddj_space/meta_projects" + File.separator + projectName));
        String output = executor.exec(command).replaceAll("\\s", "");
        return output;
    }

    public static String generateRegressionUUID() {
        UUID uuid = UUID.randomUUID(); // 生成随机UUID
        return uuid.toString();
    }

    public static String queryProjectUuid(Connection targetConn, String project_full_name) {
        String fieldValue = null;
        Statement statement = null;
        ResultSet resultSet = null;

        try {
            // 连接数据库
            statement = targetConn.createStatement();
            // 执行查询语句
            String query = "SELECT uuid FROM " + projectTableName + " WHERE project_full_name = '" + project_full_name + "'";
            resultSet = statement.executeQuery(query);
            // 提取查询结果
            if (resultSet.next()) {
                fieldValue = resultSet.getString("uuid");
            }
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            // 关闭数据库资源
            try {
                if (resultSet != null) {
                    resultSet.close();
                }
                if (statement != null) {
                    statement.close();
                }
            } catch (SQLException e) {
                e.printStackTrace();
            }
        }

        return fieldValue;
    }
}
