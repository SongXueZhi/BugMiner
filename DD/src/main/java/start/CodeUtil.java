package start;

import org.eclipse.jdt.core.JavaCore;
import org.eclipse.jdt.core.dom.*;
import start.ast.JdtClassRetriever;
import start.ast.JdtMethodRetriever;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.*;

public class CodeUtil {
	public static CompilationUnit parseCompliationUnit(String fileContent) {

		ASTParser parser = ASTParser.newParser(AST.JLS11); // handles JDK 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
		parser.setSource(fileContent.toCharArray());
		// In order to parse 1.6 code, some compiler options need to be set to 1.6
		Map<String, String> options = JavaCore.getOptions();
		JavaCore.setComplianceOptions(JavaCore.VERSION_1_8, options);
		parser.setCompilerOptions(options);

		CompilationUnit result = (CompilationUnit) parser.createAST(null);
		return result;
	}

	public static List<Methodx> getAllMethodWithoutInner(String codeContent) {
		List<Methodx> methods = new ArrayList<>();
		JdtMethodRetriever retriever = new JdtMethodRetriever();
		CompilationUnit unit = parseCompliationUnit(codeContent);
		unit.accept(retriever);
		List<MethodDeclaration> methodNodes = retriever.getMemberList();
		for (ASTNode node : methodNodes) {
		    if (!(node.getParent().getParent() instanceof CompilationUnit) ){
		        continue;
            }
			MethodDeclaration methodDeclaration = (MethodDeclaration) node;
			String simpleName = methodDeclaration.getName().toString();
			String signature =getSignature(methodDeclaration);
			int startLine = unit.getLineNumber(methodDeclaration.getStartPosition());
			int endLine = unit.getLineNumber(methodDeclaration.getStartPosition() + node.getLength());
			methods.add(new Methodx(signature, startLine, endLine, simpleName, methodDeclaration));
		}
		return methods;
	}


	public static List<Methodx> getAllMethod(String codeContent) {
		CompilationUnit unit = parseCompliationUnit(codeContent);
		return getAllMethod(unit);
	}

	public static List<Methodx> getAllMethod(CompilationUnit unit) {
		List<Methodx> methods = new ArrayList<>();
		JdtMethodRetriever retriever = new JdtMethodRetriever();
		unit.accept(retriever);
		List<MethodDeclaration> methodNodes = retriever.getMemberList();
		for (ASTNode node : methodNodes) {
			MethodDeclaration methodDeclaration = (MethodDeclaration) node;
			String simpleName = methodDeclaration.getName().toString();
			String signature = getSignature(methodDeclaration);
			int startLine = unit.getLineNumber(methodDeclaration.getStartPosition());
			int endLine = unit.getLineNumber(methodDeclaration.getStartPosition() + node.getLength());
			methods.add(new Methodx(signature, startLine, endLine, simpleName, methodDeclaration));
		}
		return methods;
	}
	public static String getQualityClassName(String codeContent) {
		String result;
		CompilationUnit unit = parseCompliationUnit(codeContent);
		JdtClassRetriever retriever = new JdtClassRetriever();
		unit.accept(retriever);
		result = retriever.getQualityName();
		return result;
	}

	public static  String getSignature(MethodDeclaration methodDeclaration){
		String simpleName = methodDeclaration.getName().toString();
		List<ASTNode> parameters = ListUtil.castList(ASTNode.class, methodDeclaration.parameters());
		// SingleVariableDeclaration
		StringJoiner sj = new StringJoiner(",", simpleName + "(", ")");
		for (ASTNode param : parameters) {
			sj.add(param.toString());
		}
		return  sj.toString();
	}

}
