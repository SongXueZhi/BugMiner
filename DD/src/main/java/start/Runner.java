package start;


import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeoutException;

public class Runner {
    protected List<String> errorMessages;
    protected File revDir;
    protected String testCase;

    public Runner(File revDir, String testCase) {
        this.revDir = revDir;
        this.testCase = testCase;
    }

    public List<String> getErrorMessages() {
        if (this.errorMessages == null) {
            this.run();
        }
        return this.errorMessages;
    }


    public void run() {
        String buildCommand = "mvn compile";
        String testCommand = "mvn test -Dtest=" + this.testCase + " " + "-Dmaven.test.failure.ignore=true";
        try {
            new Executor().setDirectory(this.revDir).exec(buildCommand);
            new Executor().setDirectory(this.revDir).exec(testCommand, 5);
        } catch (TimeoutException ex) {
        } catch (Exception ex) {
            ex.printStackTrace();
        }
    }
}
