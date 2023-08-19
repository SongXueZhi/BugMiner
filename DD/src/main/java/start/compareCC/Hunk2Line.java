package start.compareCC;

import com.opencsv.CSVWriter;

import java.io.*;

/**
 * @author lsn
 * @date 2023/6/19 8:19 PM
 */
public class Hunk2Line {
    static String dataPath = "/Users/lsn/ddj_space/data_defects4j";
    static String diffPath = "/Users/lsn/ddj_space/diff_defects4j";

    public static void main(String[] args) throws IOException {

        CSVWriter writer = new CSVWriter(new FileWriter("data_defects4j.csv"));
        String[] header = {"ID", "tool", "ccFile","ccGroup", "ccHunk", "ccLine",
                "diffFile",  "diffGroup", "diffHunk", "diffLine", "groupCompare", "hunkCompare", "lineCompare"};
        writer.writeNext(header);

        File directory = new File(dataPath);
        File[] files = directory.listFiles();

        if (files != null) {
            for (File file : files) {
                if (file.isFile()) {
//                    if(!file.getName().contains("799_bic_ddj_prodd") ){
//                        continue;
//                    }
                    if(file.getName().contains(".DS_Store")){
                        continue;
                    }
                    try {
                        //System.out.println(file.getName());
                        String id = file.getName().split("_")[0];
                        String tool = file.getName().split("_")[3].substring(0,5);
                        if(tool.equals("reldd")){
                            tool = tool + "-" + file.getName().split("_")[4];
                        }

                        FileLineRangeMap lineRangeMap = getCcHunk(dataPath + File.separator + file.getName());
                        FileLineRangeMap diffLineRangeMap = getDiffHunk(diffPath + File.separator + id + "_diff_ddj_ddmin");

                        String groupCompare = lineRangeMap.getGroupNum() == 0 ? "no_cc"  :
                                (lineRangeMap.getGroupNum() == (diffLineRangeMap.getGroupNum())) ? "len_same" :
                                        (lineRangeMap.getGroupNum() < (diffLineRangeMap.getGroupNum())) ? "better" : "worse" ;
                        String hunkCompare = lineRangeMap.getHunkNum() == 0 ? "no_cc":
                                (lineRangeMap.getHunkNum() == (diffLineRangeMap.getHunkNum())) ? "len_same" :
                                        (lineRangeMap.getHunkNum() < (diffLineRangeMap.getHunkNum())) ? "better" : "worse" ;
                        String lineCompare = lineRangeMap.getTotalLineCount() == 0 ? "no_cc" : lineRangeMap.equals(diffLineRangeMap) ? "same" :
                                        (lineRangeMap.getTotalLineCount() == (diffLineRangeMap.getTotalLineCount())) ? "len_same" :
                                        (lineRangeMap.getTotalLineCount() < (diffLineRangeMap.getTotalLineCount())) ? "better" : "worse" ;

//                        System.out.println(id + "-" + tool + ": " );
//                        System.out.print("cc: " + lineRangeMap.toString() );
//                        System.out.print("diff: " + diffLineRangeMap.toString() );

                        writer.writeNext(new String[]{id, tool,
                                String.valueOf(lineRangeMap.getFileCount()), String.valueOf(lineRangeMap.getGroupNum()), String.valueOf(lineRangeMap.getHunkNum()), String.valueOf(lineRangeMap.getTotalLineCount()),
                                String.valueOf(diffLineRangeMap.getFileCount()), String.valueOf(diffLineRangeMap.getGroupNum()), String.valueOf(diffLineRangeMap.getHunkNum()), String.valueOf(diffLineRangeMap.getTotalLineCount()),
                                groupCompare, hunkCompare, lineCompare,
                        });

                    }catch (Exception e){
                        System.out.println("error: " + file.getName());
                        e.printStackTrace();
                    }
                }
            }
        }
        writer.close();
    }

//    public static void main(String[] arge){
//        FileLineRangeMap lineRangeMap = getCcHunk("id.txt");
//        System.out.println(lineRangeMap.toString());
//    }

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
            int cc = 10000;
            while ((line = bufferedReader.readLine()) != null) {
                if(dataFilePath.contains("reldd") && line.startsWith("cc")){
                    cc = Math.min(cc,Integer.parseInt(line.replace("cc", "").trim().split("cp: ")[0]));
                }
                //todo 对于defetcs4j是FAIL
                if(dataFilePath.contains("reldd") && line.contains(":FAIL")){
                    String set = line.split(":")[0].trim();
                    cc = Math.min(cc,set.split(",").length);
                }
                if(dataFilePath.contains("reldd") && line.startsWith("ungrouped (")){
                    if(Integer.parseInt(line.split("\\(")[1].split("\\)")[0]) == 1){
                        cc = 1;
                    }
                }
                if(!dataFilePath.contains("reldd") && line.startsWith("ungrouped components (")){
                    fileLineRangeMap.setGroupNum(Integer.parseInt(line.split("\\(")[1].split("\\)")[0]));
                }
                if(line.contains("***")){
                    fileName = line.replace("***", "").trim();
                }
                if(line.contains("*] HUNK")){
                    int[] lineRange = splitLineRange(line.split("HUNK ")[1].split("cp:")[0]);
                    if(lineRange == null){
                        continue;
                    }
                    fileLineRangeMap.setHunkNum(fileLineRangeMap.getHunkNum() + 1);
                    fileLineRangeMap.addLineRange(fileName, lineRange[0], lineRange[1]);
                }
            }

            if(dataFilePath.contains("reldd")){
                if(cc == 10000){
                    cc = 0;
                }
                fileLineRangeMap.setGroupNum(cc);
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
                if(line.startsWith("ungrouped (")){
                    fileLineRangeMap.setGroupNum(Integer.parseInt(line.split("\\(")[1].split("\\)")[0]));
                }
                if(line.startsWith(" HUNK")){
                    String fileName = splitFileName(line.split("HUNK ")[1]);
                    int[] lineRange = splitLineRange(line.split("HUNK ")[1]);
                    if(fileName == null || fileName.isEmpty() || fileName.equals("") || lineRange == null){
                        continue;
                    }
                    fileLineRangeMap.setHunkNum(fileLineRangeMap.getHunkNum() + 1);
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
            lineRange = lineRangeArray[3].replace("[","");
        }
        else if(lineRangeArray[1].equals("INS")){
            // (0) INS File [None]-[src/main/java/org/dbtools/query/shared/QueryCompareType.java]
            if(lineRangeArray[2].equals("File")){
                //None
                return new int[]{0, 0};
            }
            lineRange = lineRangeArray[4].split("\\[")[1];
        }
        else if( lineRangeArray[1].equals("MOV")){
            if(lineRangeArray[2].equals("File")){
                //None
                return new int[]{0, 0};
            }
            lineRange = lineRangeArray[4].split("\\[")[1];
        }
        else if(lineRangeArray[1].equals("REL")) {
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
        }else if(lineRangeArray[1].equals("MOV") && lineRangeArray[2].equals("File")){
            fileName = lineRangeArray[3].split("\\]")[0].replace("[", "");
        }else if(lineRangeArray[1].equals("INS") && lineRangeArray[2].equals("File")){
            fileName = lineRangeArray[3].split("\\]")[1].replace("[", "").replace("-", "");
        } else if(lineRangeArray[1].equals("INS")  ) {
            //297:4-306:4
            fileName = lineRangeArray[5].split("\\]")[0];
        }else if(lineRangeArray[1].equals("REL")){
            fileName = lineRangeArray[5].split("\\]")[0];
        }else if(lineRangeArray[1].equals("MOV") ){
            fileName = lineRangeArray[5].split("\\]")[0];
        }
        return fileName;
    }
}
