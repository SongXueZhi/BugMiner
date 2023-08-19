package start;

import org.apache.commons.cli.*;

import java.io.File;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

/**
 * @Author: sxz
 * @Date: 2022/12/26/18:56
 * @Description:
 */
public class Main {
    private static Options OPTIONS = new Options();
    private static CommandLine commandLine;
    private static String HELP_STRING = null;
    private final static String CONFIG_LONG_OPT="configPath";
//    public static String workSpacePath =  System.getProperty("user.home") + File.separator + "ddj_space";
    public static String workSpacePath = "/home/sxz/ddj_space";//79服务器
//    public static String workSpacePath =  System.getProperty("user.home") + File.separator + "dd" +  File.separator + "ddj_space" ;//95服务器
//    public static String workSpacePath =  System.getProperty("user.home") + File.separator + "miner" ;//99服务器
    static Reducer reducer = new Reducer();
    static Migrator migrator = new Migrator();
    static RegCleaner regCleaner =new RegCleaner();

    public static void main(String[] args) throws Exception {
        CommandLineParser commandLineParser = new DefaultParser();
        // help
        OPTIONS.addOption("help","usage help");
        // port
        OPTIONS.addOption(Option.builder("p").hasArg(true).longOpt(CONFIG_LONG_OPT).type(String.class)
                .desc("Configuration file path").build());
        try {
            commandLine = commandLineParser.parse(OPTIONS, args);
            workSpacePath = commandLine.getOptionValue(CONFIG_LONG_OPT);
        } catch (ParseException e) {
            System.exit(0);
        }
        doClean();
    }
    static void doClean(){
        RegCleaner regCleaner = new RegCleaner();
        //步骤1： 处理数据，从数据库里拿数据，数据按照项目名组合
        Map<String,List<Regression>>  regsMap  = MysqlManager.selectRegressions("select * from regressions_all");
        //步骤2： 处理每一个项目
        File projectDir;
        String[] childs = null;
        for (Map.Entry<String, List<Regression>> entry : regsMap.entrySet()) {
            projectDir = SourceManager.getProjectDir(entry.getKey());
            //如果文件夹为空，说明处理失败
            childs = projectDir.list();
            if( childs==null || childs.length<=0){
                System.out.println(entry.getKey());
                continue;
            }
            //步骤3： 处理项目的每一个regression
            for (Regression regression: entry.getValue()){
                // 步骤1 checkout bug的四个版本。
                Revision bfc = new Revision(regression.getBfc(),"bfc");
                bfc.setLocalCodeDir(SourceManager.checkout(regression.getId(), bfc, projectDir,entry.getKey()));
                regression.setBfcRev(bfc);

                Revision buggy = new Revision(regression.getBfc()+"~1","buggy");
                buggy.setLocalCodeDir(SourceManager.checkout(regression.getId(),buggy, projectDir, entry.getKey()));
                regression.setBuggyRev(buggy);

                Revision bic = new Revision(regression.getBic(),"bic");
                bic.setLocalCodeDir(SourceManager.checkout(regression.getId(),bic, projectDir, entry.getKey()));
                regression.setBicRev(bic);

                Revision work = new Revision(regression.getWork(),"work");
                work.setLocalCodeDir(SourceManager.checkout(regression.getId(),work, projectDir, entry.getKey()));
                regression.setWorkRev(work);

                //步骤2 迁移测试用例
                List<Revision> needToTestMigrateRevisionList = Arrays.asList(new Revision[]{buggy, bic, work});
                migrateTestAndDependency(bfc, needToTestMigrateRevisionList, regression.getTestCaseString());

                regCleaner.clean(regression);
                //步骤3 clean
                System.out.println("");
                //步骤4， 插入新的数据库
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
