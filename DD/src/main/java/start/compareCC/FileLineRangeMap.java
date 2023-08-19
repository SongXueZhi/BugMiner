package start.compareCC;

import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

/**
 * @author lsn
 * @date 2023/4/18 7:21 PM
 */
public class FileLineRangeMap {
    private Map<String, LineRangeList> fileLineRangeMap;

    private int hunkNum ;

    private int groupNum ;

    public int getHunkNum() {
        return hunkNum;
    }

    public void setHunkNum(int hunkNum) {
        this.hunkNum = hunkNum;
    }

    public Map<String, LineRangeList> getFileLineRangeMap() {
        return fileLineRangeMap;
    }

    public int getGroupNum() {
        return groupNum;
    }

    public void setGroupNum(int groupNum) {
        this.groupNum = groupNum;
    }

    public FileLineRangeMap() {
        fileLineRangeMap = new HashMap<>();
        hunkNum = 0;
        groupNum = 0;
    }

    public void addLineRange(String fileName, int start, int end) {
        LineRange range = new LineRange(start, end);
        if (fileLineRangeMap.containsKey(fileName)) {
            LineRangeList rangeList = fileLineRangeMap.get(fileName);
            rangeList.addLineRange(range);
        } else {
            LineRangeList rangeList = new LineRangeList();
            rangeList.addLineRange(range);
            fileLineRangeMap.put(fileName, rangeList);
        }
    }

    public int getFileCount() {
        return fileLineRangeMap.size();
    }

    public int getFileLineCount(String fileName) {
        if (fileLineRangeMap.containsKey(fileName)) {
            LineRangeList lineRanges = fileLineRangeMap.get(fileName);
            int totalLineCount = 0;
            for (LineRange lineRange : lineRanges.getLineRanges()) {
                totalLineCount += lineRange.getEndLine() - lineRange.getStartLine() + 1;
            }
            return totalLineCount;
        }
        return 0;
    }

    public int getTotalLineCount() {
        int thisTotalLineCount = 0;
        for (String fileName : fileLineRangeMap.keySet()) {
            thisTotalLineCount += getFileLineCount(fileName);
        }
        return thisTotalLineCount;
    }

    public boolean contains(FileLineRangeMap other) {
        // 对比两个 FileLineRangeMap 中的每个文件名
        for (String fileName : other.fileLineRangeMap.keySet()) {
            // 如果当前 FileLineRangeMap 不包含 other 中的文件名，则直接返回 false
            if (!fileLineRangeMap.containsKey(fileName)) {
                return false;
            }

            // 获取当前 FileLineRangeMap 中的 LineRangeList 和 other 中的 LineRangeList
            LineRangeList thisLineRangeList = fileLineRangeMap.get(fileName);
            LineRangeList otherLineRangeList = other.fileLineRangeMap.get(fileName);

            // 对比 LineRangeList 是否相等
            if (!thisLineRangeList.equals(otherLineRangeList)) {
                return false;
            }
        }

        // 如果所有的文件名和 LineRangeList 都相等，则说明两个 FileLineRangeMap 是包含关系
        return true;
    }

    public int compareSize(FileLineRangeMap other) {
        return Integer.compare(getTotalLineCount(), other.getTotalLineCount());
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        for (String fileName : fileLineRangeMap.keySet()) {
            LineRangeList rangeList = fileLineRangeMap.get(fileName);
            sb.append(fileName).append(": ").append(rangeList.toString()).append("\n");
        }
        return sb.toString();
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (!(obj instanceof FileLineRangeMap)) {
            return false;
        }

        FileLineRangeMap other = (FileLineRangeMap) obj;

        if (fileLineRangeMap.size() != other.fileLineRangeMap.size()) {
            return false;
        }

        for (String fileName : fileLineRangeMap.keySet()) {
            if (!other.fileLineRangeMap.containsKey(fileName)) {
                return false;
            }

            LineRangeList thisLineRangeList = fileLineRangeMap.get(fileName);
            LineRangeList otherLineRangeList = other.fileLineRangeMap.get(fileName);

            if (!thisLineRangeList.equals(otherLineRangeList)) {
                return false;
            }
        }

        return true;
    }

    @Override
    public int hashCode() {
        return Objects.hash(fileLineRangeMap);
    }

    public static void main(String[] args) {
        String input = "[0*] HUNK (4) DEL PrimaryMethodInvocationStatement [1006:8-1006:51 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[964:85-1128:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [1*] HUNK (7) DEL PrimaryMethodInvocationStatement [1009:8-1009:52 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[964:85-1128:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [2*] HUNK (6) DEL PrimaryMethodInvocationStatement [1010:8-1010:72 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[964:85-1128:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [3*] HUNK (3) DEL PrimaryMethodInvocationStatement [1011:8-1011:41 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[964:85-1128:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [6*] HUNK (5) DEL SimpleMethodInvocationStatement [1017:8-1017:70 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[964:85-1128:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [7*] HUNK (4) DEL PrimaryMethodInvocationStatement [1018:8-1018:33 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[964:85-1128:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [8*] HUNK (7) DEL PrimaryMethodInvocationStatement [1019:8-1019:78 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[964:85-1128:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [10*] HUNK (6) DEL PrimaryMethodInvocationStatement [1021:8-1021:98 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[964:85-1128:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [11*] HUNK (13) DEL PrimaryMethodInvocationStatement [1022:8-1023:108 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[964:85-1128:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [12*] HUNK (7) DEL PrimaryMethodInvocationStatement [1024:8-1024:63 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[964:85-1128:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [13*] HUNK (10) DEL PrimaryMethodInvocationStatement [1026:8-1026:68 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[964:85-1128:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [14*] HUNK (7) DEL PrimaryMethodInvocationStatement [1027:8-1027:62 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[964:85-1128:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [15*] HUNK (23) DEL IfStatement [1028:8-1032:8 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[964:85-1128:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [17*] HUNK (4) DEL PrimaryMethodInvocationStatement [1035:8-1035:39 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[964:85-1128:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [18*] HUNK (3) DEL PrimaryMethodInvocationStatement [1037:8-1037:37 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[964:85-1128:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [17*] HUNK (4) INS PrimaryMethodInvocationStatement [964:85-1151:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[1001:8-1001:43 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [1*] HUNK (7) INS PrimaryMethodInvocationStatement [964:85-1151:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[997:8-997:52 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [2*] HUNK (6) INS PrimaryMethodInvocationStatement [964:85-1151:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[998:8-998:72 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [3*] HUNK (3) INS PrimaryMethodInvocationStatement [964:85-1151:4 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[999:8-999:43 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [3*] HUNK (3) MOV PrimaryMethodInvocationStatement [1011:8-1011:41 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[999:8-999:43 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [3*] HUNK (0) REL Name [1011:24-1011:39 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[999:24-999:41 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [17*] HUNK (0) REL FieldAccess [1035:25-1035:28 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[1001:25-1001:33 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]\n" +
                "  [17*] HUNK (0) REL Name [1035:31-1035:37 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]-[1001:36-1001:41 src/main/java/com/alibaba/fastjson/parser/deserializer/ASMDeserializerFactory.java]" +
                "";
        FileLineRangeMap fileLineRangeMap = new FileLineRangeMap();

        String[] lines = input.split("\n");
        for (String line : lines) {
            if(line.contains("*] HUNK")){
                String[] parts = line.trim().split("\\[|\\]|\\s|\\-|:|\\ ");
                String fileName = parts[12];
                int start = Integer.parseInt(parts[8]);
                int end = Integer.parseInt(parts[10]);
                fileLineRangeMap.addLineRange(fileName, start, end);
            }

        }

        System.out.println(fileLineRangeMap.toString());
    }

}
