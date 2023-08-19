package start.diffLine;

import com.opencsv.CSVWriter;
import start.*;

import java.io.*;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * @author lsn
 * @date 2023/4/17 3:05 PM
 */
public class CalDiffLines {

    public static void main(String[] args) throws IOException {
        CSVWriter writer = new CSVWriter(new FileWriter("diffNum.csv"));
        String[] header = {"ID", "diffFile", "diffHunk", "changeLineNum"};
        writer.writeNext(header);

        String sql = "select * from regressions_all where id = 666";
        //String sql = "select * from regressions_all where is_clean=1 and is_dirty=0";
        List<Regression> regressions  = MysqlManager.selectRegressionstoList(sql);
        System.out.println("regression size: " + regressions.size());
        for(Regression regression : regressions){
            System.out.println("regression id: " + regression.getId());
            String projectName = regression.getProject_full_name();
            String id = regression.getId();
            File projectDir = SourceManager.getProjectDir(projectName);
            String result = diff(regression.getBic(), regression.getWork(), projectDir.getAbsolutePath());
            ArrayList<DiffFile> diffFiles = buildDiffObject(result);
            int totalDiffHunkNum = 0;
            int totalChangeLineNum = 0;
            for(DiffFile diffFile : diffFiles){
                totalDiffHunkNum += diffFile.getDiffHunks().size();
                for(DiffHunk diffHunk : diffFile.getDiffHunks()){
                    totalChangeLineNum += diffHunk.getChangeLineNum();
                }
            }
            String[] line = {id, String.valueOf(diffFiles.size()), String.valueOf(totalDiffHunkNum), String.valueOf(totalChangeLineNum)};
            writer.writeNext(line);
        }
        writer.close();
    }

    public static String diff(String bicId, String workId, String projectDir) {
        String cmd = "git diff "+bicId+ " "+workId;
        String result = execCmd(cmd, new File(projectDir));
        return result;
    }

    public static ArrayList<DiffFile> buildDiffObject(String result){
        String[] filesResult = result.split("diff --git");
        ArrayList<DiffFile> diffFiles = new ArrayList<>();
        for(String fileResult : filesResult){
            ArrayList<DiffHunk> diffHunks = new ArrayList<>();
            Pattern pattern = Pattern.compile(" a/(.*?) b/(.*?)\\n");
            Matcher matcher = pattern.matcher(fileResult);
            if (matcher.find() && (matcher.group(1).contains("src/main/java/") || matcher.group(2).contains("src/main/java/") )) {
                String aPath = matcher.group(1); // a 文件的路径
                String bPath = matcher.group(2); // b 文件的路径

                DiffFile diffFile = new DiffFile();
                diffFile.setFileNameA(aPath);
                diffFile.setFileNameB(bPath);
                System.out.println(aPath + " " + bPath);
                String[] hunksResult = fileResult.split("(?<=\\n)(?=@@)");
                for (String hunkResult : hunksResult) {
                    if (hunkResult.startsWith("@@")) {
                        DiffHunk diffHunk = new DiffHunk();
                        diffHunk.setHunkName(hunkResult.split("@@")[1].trim());
                        System.out.println(diffHunk.getHunkName());

                        int insertNum = 0;
                        int deleteNum = 0;
                        String[] hunkLines = hunkResult.split("\\n");
                        for (String hunkLine : hunkLines) {
                            if (hunkLine.startsWith("-") && !ifCommentsAndEmptyLines(hunkLine.replace("-", ""))) {
                                deleteNum++;
                            } else if (hunkLine.startsWith("+") && !ifCommentsAndEmptyLines(hunkLine.replace("+", ""))) {
                                insertNum++;
                            }
                        }
                        diffHunk.setDeleteNum(deleteNum);
                        diffHunk.setInsertNum(insertNum);
                        System.out.println(deleteNum + " " + insertNum);
                        diffHunks.add(diffHunk);
                    }
                }
                diffFile.setDiffHunks(diffHunks);
                diffFiles.add(diffFile);
            }
        }
        return diffFiles;
    }

    public static String execCmd(String cmd, File dir) {
        StringBuilder result = new StringBuilder();

        Process process = null;
        BufferedReader bufrIn = null;
        BufferedReader bufrError = null;

        try {
            process = Runtime.getRuntime().exec(cmd, null, dir);
            bufrIn = new BufferedReader(new InputStreamReader(process.getInputStream(), "UTF-8"));
            bufrError = new BufferedReader(new InputStreamReader(process.getErrorStream(), "UTF-8"));
            String line = null;
            while ((line = bufrIn.readLine()) != null) {
                result.append(line).append('\n');
            }
            while ((line = bufrError.readLine()) != null) {
                result.append(line).append('\n');
            }
        } catch (Exception e){
            e.printStackTrace();
        }finally {
            closeStream(bufrIn);
            closeStream(bufrError);
            if (process != null) {
                process.destroy();
            }
        }
        return result.toString();
    }

    private static void closeStream(Closeable stream) {
        if (stream != null) {
            try {
                stream.close();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    public static boolean ifCommentsAndEmptyLines(String line) {
        boolean ifCommentsAndEmptyLines = false;
        String trimmedLine = line.trim();
        if (trimmedLine.startsWith("/*") || trimmedLine.startsWith("*") || trimmedLine.startsWith("//") || trimmedLine.isEmpty()) {
            ifCommentsAndEmptyLines = true;
        }
        return ifCommentsAndEmptyLines;
    }

    public static void clearComment(File file) throws IOException {

        //根据对应的编码格式读取
        BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(file), "UTF-8"));
        StringBuffer content = new StringBuffer();
        String tmp = null;
        while ((tmp = reader.readLine()) != null) {
            content.append(tmp);
            content.append("\n");
        }
        String target = content.toString();

        String s = target.replaceAll("\\/\\/[^\\n]*|\\/\\*([^\\*^\\/]*|[\\*^\\/*]*|[^\\**\\/]*)*\\*+\\/|\\/\\*\\*([^\\*^\\/]*|[\\*^\\/*]*|[^\\**\\/]*)*\\*+\\/", "");
//          String s = target.replace("\\/\\*[\\w\\W]*?\\*\\/|\\/\\/.*","");
        s= s.replaceAll("\\{\\+\\s*\\+\\}","").replaceAll("\\{\\+\\s*\n","");//.replaceAll("\\+\\}","");
        s= s.replaceAll("\\[\\-\\s*\\-\\]","").replaceAll("\\[\\-\\s*\n","");//.replaceAll("\\-\\]","");
//          s=q;
        //使用对应的编码格式输出  \\s*|\t|\r|\n
        BufferedWriter out = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(file), "UTF-8"));
        out.write(s);
        out.flush();
        out.close();
    }

    public static String removeCommentsAndEmptyLines(String code) {
        StringBuilder sb = new StringBuilder();
        String[] lines = code.split("\n");
        boolean insideBlockComment = false;
        for (String line : lines) {
            String trimmedLine = line.trim();
            if (trimmedLine.startsWith("/*")) {
                insideBlockComment = true;
            }
            if (!insideBlockComment && !trimmedLine.startsWith("//") && !trimmedLine.isEmpty()) {
                sb.append(line).append("\n");
            }
            if (trimmedLine.endsWith("*/")) {
                insideBlockComment = false;
            }
        }
        return sb.toString();
    }

    public static int getChangeLineNum(ArrayList<DiffFile> diffFiles){
        int changeLineNum = 0;
        for(DiffFile diffFile : diffFiles){
            for(DiffHunk diffHunk : diffFile.getDiffHunks()){
                changeLineNum += diffHunk.getChangeLineNum();
            }
        }
        System.out.println(changeLineNum);
        return changeLineNum;
    }

}
