package start.compareCC;

import com.opencsv.CSVWriter;

import java.io.*;

/**
 * @author lsn
 * @date 2023/4/18 5:26 PM
 */
public class CompareCC {
    static String dataPath = "/Users/lsn/ddj_space/data0420";
    static String diffPath = "/Users/lsn/ddj_space/diff0420";

    public static void main(String[] args)  throws IOException {

        CSVWriter writer = new CSVWriter(new FileWriter("compare.csv"));
        String[] header = {"ID", "ddminFile", "proddFile", "diffFile", "ddminLine",  "proddLine", "diffLine"
                ,"ddmin_compare","prodd_compare"};
        writer.writeNext(header);

        File directory = new File(diffPath);
        File[] files = directory.listFiles();

        if (files != null) {
            for (File file : files) {
                if (file.isFile()) {
//                    if(!file.getName().contains("JacksonCore21")){
//                        continue;
//                    }
                    System.out.println(file.getName());
                    String id = file.getName().split("_")[0];
                    FileLineRangeMap ddminLineRangeMap = getCcHunk(dataPath + File.separator + id + "_defects4j_ddj_ddmin");
                    FileLineRangeMap proddLineRangeMap = getCcHunk(dataPath + File.separator + id + "_defects4j_ddj_prodd");
                    FileLineRangeMap diffLineRangeMap = getDiffHunk(diffPath + File.separator + id + "_diff_ddj_ddmin");

                    String ddminCompare = ddminLineRangeMap.equals(diffLineRangeMap) ? "same" :
                            (ddminLineRangeMap.getTotalLineCount() == (diffLineRangeMap.getTotalLineCount())) ? "len_same" :
                                    (ddminLineRangeMap.getTotalLineCount() < (diffLineRangeMap.getTotalLineCount())) ? "ddmin_better" : "patch_better" ;

                    String proddCompare = proddLineRangeMap.equals(diffLineRangeMap) ? "same" :
                            (proddLineRangeMap.getTotalLineCount() == (diffLineRangeMap.getTotalLineCount())) ? "len_same" :
                                    (proddLineRangeMap.getTotalLineCount() < (diffLineRangeMap.getTotalLineCount())) ? "prodd_better" : "patch_better" ;


                    String[] line = {id, String.valueOf(ddminLineRangeMap.getFileCount()), String.valueOf(proddLineRangeMap.getFileCount()),
                            String.valueOf(diffLineRangeMap.getFileCount()), String.valueOf(ddminLineRangeMap.getTotalLineCount()),
                            String.valueOf(proddLineRangeMap.getTotalLineCount()), String.valueOf(diffLineRangeMap.getTotalLineCount()),
                            ddminCompare, proddCompare,
                    };
                    writer.writeNext(line);

                    System.out.println("ddminLineRangeMap: \n" + ddminLineRangeMap);
                    System.out.println("proddLineRangeMap: \n" + proddLineRangeMap);
                    System.out.println("diffLineRangeMap: \n" + diffLineRangeMap);
                }
            }
        }

        writer.close();
    }

    public static FileLineRangeMap getCcHunk(String dataFilePath) {
        FileLineRangeMap fileLineRangeMap = new FileLineRangeMap();
        try {
            // 创建 FileReader 对象读取文件
            FileReader fileReader = new FileReader(dataFilePath);
            // 创建 BufferedReader 对象以便按行读取文件
            BufferedReader bufferedReader = new BufferedReader(fileReader);
            String line;
            // 按行读取文件内容
            String fileName = "";
            while ((line = bufferedReader.readLine()) != null) {
                if(line.contains("***")){
                    fileName = line.replace("***", "").trim();
                }
                if(line.contains("*] HUNK")){
                    int[] lineRange = splitLineRange(line.split("HUNK ")[1]);
                    if(lineRange == null){
                        continue;
                    }
                    fileLineRangeMap.addLineRange(fileName, lineRange[0], lineRange[1]);
                }
            }
            bufferedReader.close(); // 关闭 BufferedReader
        }
        catch (FileNotFoundException e) {
            System.out.println("文件不存在：" + dataFilePath); // 输出文件不存在提示
        }
        catch (IOException e) {
            e.printStackTrace();
        }
        return fileLineRangeMap;
    }


    public static FileLineRangeMap getDiffHunk(String diffFilePath) {
        FileLineRangeMap fileLineRangeMap = new FileLineRangeMap();
        try {
            // 创建 FileReader 对象读取文件
            FileReader fileReader = new FileReader(diffFilePath);
            // 创建 BufferedReader 对象以便按行读取文件
            BufferedReader bufferedReader = new BufferedReader(fileReader);
            String line;
            // 按行读取文件内容
            while ((line = bufferedReader.readLine()) != null) {
                if(line.contains("HUNK")){
                    String fileName = splitFileName(line.split("HUNK ")[1]);
                    int[] lineRange = splitLineRange(line.split("HUNK ")[1]);
                    fileLineRangeMap.addLineRange(fileName, lineRange[0], lineRange[1]);
                }
            }
            bufferedReader.close(); // 关闭 BufferedReader
        }
        catch (FileNotFoundException e) {
            System.out.println("文件不存在：" + diffFilePath); // 输出文件不存在提示
        }
        catch (IOException e) {
            e.printStackTrace();
        }
        return fileLineRangeMap;
    }

    public static int[] splitLineRange(String line){
        // (7) DEL IfStatement [305:8-307:8 src/main/java/com/fasterxml/jackson/core/json/UTF8StreamJsonParser.java]-[297:4-306:4 src/main/java/com/fasterxml/jackson/core/json/UTF8StreamJsonParser.java]
        String[] lineRangeArray = line.trim().split(" ");
        String lineRange = "";
        if(lineRangeArray[2].contains("Auxfile")){
            return null;
        }
        if(lineRangeArray[1].equals("DEL")){
            //(36) DEL File [src/main/java/org/apache/commons/codec/binary/CharSequenceUtils.java]-[None]
            if(lineRangeArray[2].equals("File")){
                //None
                return new int[]{0, 0};
            }
            //305:8-307:8
            lineRange = lineRangeArray[3].replace("[","");
        }else if(lineRangeArray[1].equals("INS") || lineRangeArray[1].equals("REL") || lineRangeArray[1].equals("MOV") ) {
            //297:4-306:4
            lineRange = lineRangeArray[4].split("\\[")[1];
        }
        String start = lineRange.split("-")[0].split(":")[0];
        String end = lineRange.split("-")[1].split(":")[0];
        return new int[]{Integer.parseInt(start), Integer.parseInt(end)};
    }

    public static String splitFileName(String line){
        // (7) DEL IfStatement [305:8-307:8 src/main/java/com/fasterxml/jackson/core/json/UTF8StreamJsonParser.java]-[297:4-306:4 src/main/java/com/fasterxml/jackson/core/json/UTF8StreamJsonParser.java]
        String[] lineRangeArray = line.trim().split(" ");
        String fileName = "";
        if(lineRangeArray[2].contains("Auxfile")){
            return null;
        }
        if(lineRangeArray[1].equals("DEL")){
            //(36) DEL File [src/main/java/org/apache/commons/codec/binary/CharSequenceUtils.java]-[None]
            if(lineRangeArray[2].equals("File")){
                fileName = lineRangeArray[3].split("-")[0].replace("[", "").replace("]", "");
            }else{
                //305:8-307:8
                fileName = lineRangeArray[4].split("\\]")[0];
            }
        }else if(lineRangeArray[1].equals("INS") || lineRangeArray[1].equals("REL") || lineRangeArray[1].equals("MOV") ) {
            //297:4-306:4
            fileName = lineRangeArray[5].split("\\]")[0];
        }
        return fileName;
    }

}
