package start;

import java.io.File;
import java.util.Arrays;
import java.util.List;

/**
 * @author lsn
 * @date 2023/4/13 8:12 PM
 */
public class Checkout {

    static Reducer reducer = new Reducer();
    static Migrator migrator = new Migrator();

    public static void main(String[] args) {
        String sql = "select * from regressions_all where id = 45";
        //String sql = "select * from regressions_all where is_clean=1 and is_dirty=0";
        List<Regression> regressions  = MysqlManager.selectRegressionstoList(sql);
        System.out.println("regression size: " + regressions.size());
        for (int i = 0; i < regressions.size(); i++) {
            Regression regression = regressions.get(i);
            String projectName = regression.getProject_full_name();
            File projectDir = SourceManager.getProjectDir(projectName);
            System.out.println(regression.getId());
            try {
                String message = "bic_ddj_ddmin";

                Revision bfc = new Revision(regression.getBfc(),"bfc");
                bfc.setLocalCodeDir(SourceManager.checkout(regression.getId(), bfc, projectDir, message, projectName));
                regression.setBfcRev(bfc);
                Revision buggy = new Revision(regression.getBfc()+"~1","buggy");
                buggy.setLocalCodeDir(SourceManager.checkout(regression.getId(),buggy, projectDir, message,projectName));
                regression.setBuggyRev(buggy);

                Revision bic = new Revision(regression.getBic(),"ric");
                bic.setLocalCodeDir(SourceManager.checkout(regression.getId(),bic, projectDir, message,projectName));
                regression.setBicRev(bic);

                Revision work = new Revision(regression.getWork(),"work");
                work.setLocalCodeDir(SourceManager.checkout(regression.getId(),work, projectDir, message,projectName));
                regression.setWorkRev(work);

                //步骤2 迁移测试用例
                List<Revision> needToTestMigrateRevisionList = Arrays.asList(new Revision[]{buggy, bic, work});
                migrateTestAndDependency(bfc, needToTestMigrateRevisionList, regression.getTestCaseString());

                SourceManager.createShell(regression.getId(),message, projectName, bic, regression.getTestCaseString());
                SourceManager.createShell(regression.getId(),message, projectName, work, regression.getTestCaseString());
                SourceManager.createShell(regression.getId(),message, projectName, bfc, regression.getTestCaseString());
                SourceManager.createShell(regression.getId(),message, projectName, buggy, regression.getTestCaseString());

            } catch (Exception e) {
                e.printStackTrace();
            }
        }
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
