package start;

import java.sql.*;
import java.util.*;

/**
 * @Author: sxz
 * @Date: 2022/12/26/19:07
 * @Description:
 */
public class MysqlManager {
    public static final String DRIVER = "com.mysql.cj.jdbc.Driver";
    public final static String URL = "jdbc:mysql://10.176.34.99:3306/regression?useSSL=false&allowPublicKeyRetrieval" +
            "=true&characterEncoding=UTF8";
    public final static String NAME = "root";
    public final static String PWD = "110120";
    private static Connection conn = null;
    private static Statement statement = null;

    public static int calculateTotalSize(Map<?, List<?>> valueMap) {
        int totalSize = 0;
        for (List<?> list : valueMap.values()) {
            totalSize += list.size();
        }
        return totalSize;
    }


    private static void getConn() throws Exception {
        if (conn != null) {
            return;
        }
        Class.forName(DRIVER);
        conn = DriverManager.getConnection(URL, NAME, PWD);

    }

    public static void getStatement() throws Exception {
        if (conn == null) {
            getConn();
        }
        if (statement != null) {
            return;
        }
        statement = conn.createStatement();
    }

    public static void closed() {
        try {
            if (statement != null) {
                statement.close();
            }
            if (conn != null) {
                conn.close();
            }
        } catch (Exception e) {

        } finally {
            try {
                if (statement != null) {
                    statement.close();
                    statement = null;
                }
                if (conn != null) {
                    conn.close();
                    conn = null;
                }
            } catch (Exception e) {
            }
        }
    }

    public static void executeUpdate(String sql) {
        try {
            getStatement();
            statement.executeUpdate(sql);
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            closed();
        }
    }

    public static Map<String,List<Regression>> selectRegressions(String sql) {
        Map<String,List<Regression>> regressionMap = new HashMap<>();
        try {
            getStatement();
            ResultSet rs = statement.executeQuery(sql);
            String projectName="";
            while (rs.next()) {
                projectName = rs.getString("project_name");
                Regression regression = new Regression();
                regression.setId(rs.getString("id"));
                regression.setProject_full_name(projectName);
                regression.setBfc(rs.getString("bfc"));
                regression.setBic(rs.getString("bic"));
                regression.setWork(rs.getString("wc"));
                regression.setTestCaseString(rs.getString("testcase"));

                if (! regressionMap.containsKey(projectName)){
                    regressionMap.put(projectName,new LinkedList<>());
                }
                regressionMap.get(projectName).add(regression);
            }
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            closed();
        }
        return regressionMap;
    }

    public static Map<String,List<Regression>> selectCleanRegressions(String sql) {
        Map<String, List<Regression>> regressionMap = new HashMap<>();
        try {
            getStatement();
            ResultSet rs = statement.executeQuery(sql);
            String projectName = "";
            while (rs.next()) {
                projectName = rs.getString("project_name");
                Regression regression = new Regression();
                regression.setId(rs.getString("id"));
                regression.setProject_full_name(projectName);
                regression.setBfc(rs.getString("bfc"));
                regression.setBic(rs.getString("bic"));
                regression.setWork(rs.getString("wc"));
                regression.setTestCaseString(rs.getString("testcase1").split(";")[0]);
                if (!regressionMap.containsKey(projectName)) {
                    regressionMap.put(projectName, new LinkedList<>());
                }
                regressionMap.get(projectName).add(regression);
            }
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            closed();
        }
        return regressionMap;
    }

    public static List<Regression> selectRegressionstoList(String sql) {
        List<Regression> regressions = new ArrayList<>();
        try {
            getStatement();
            ResultSet rs = statement.executeQuery(sql);
            String projectName = "";
            while (rs.next()) {
                projectName = rs.getString("project_name");
                Regression regression = new Regression();
                regression.setId(rs.getString("id"));
                regression.setProject_full_name(projectName);
                regression.setBfc(rs.getString("bfc"));
                regression.setBic(rs.getString("bic"));
                regression.setWork(rs.getString("wc"));
                regression.setTestCaseString(rs.getString("testcase1").split(";")[0]);
                regressions.add(regression);
            }
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            closed();
        }
        return regressions;
    }

}
