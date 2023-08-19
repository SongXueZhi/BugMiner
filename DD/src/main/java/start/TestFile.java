package start;

import java.util.HashSet;
import java.util.Set;

public class TestFile extends ChangedFile {
	public Type type;
	private String qualityClassName;
	public Set<String> testMethods = new HashSet<>();

	public TestFile(String newPath) {
		super(newPath);
	}

	public String getQualityClassName() {
		return qualityClassName;
	}

	public void setQualityClassName(String qualityClassName) {
		this.qualityClassName = qualityClassName;
	}



}
