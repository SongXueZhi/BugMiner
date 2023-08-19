package start.DDJ;

import start.DDJ.DDJThread;

/**
 * @author lsn
 * @date 2023/3/17 10:33 AM
 */
public class TestDDJ {

    public static void main(String[] args) throws InterruptedException {

//        DDJThreadForNew ddjThread1 = new DDJThreadForNew("reldd1", "bic", true, 1,650, "log+matrix");
//        DDJThreadForNew ddjThread2 = new DDJThreadForNew("reldd1", "bic", true,1,650, "log");
//        DDJThreadForNew ddjThread3 = new DDJThreadForNew("reldd1", "bic", true,1,650, "matrix");
//        DDJThreadForNew ddjThread4 = new DDJThreadForNew("reldd2", "bic", true, 651,1700, "log+matrix");
//        DDJThreadForNew ddjThread5 = new DDJThreadForNew("reldd2", "bic", true,651,1700, "log");
//        DDJThreadForNew ddjThread6 = new DDJThreadForNew("reldd2", "bic", true,651,1700, "matrix");
//        DDJThreadForNew ddjThread7 = new DDJThreadForNew("reldd3", "bic", true, 1701,1800, "log+matrix");
//        DDJThreadForNew ddjThread8 = new DDJThreadForNew("reldd3", "bic", true,1701,1800,"log");
//        DDJThreadForNew ddjThread9 = new DDJThreadForNew("reldd3", "bic", true,1701,1800, "matrix");
//        DDJThreadForNew ddjThread1 = new DDJThreadForNew("reldd1", "bic", true, 1,650, "noconsider");
//        DDJThreadForNew ddjThread2 = new DDJThreadForNew("reldd1", "bic", true,1,650, "nostart");
//        DDJThreadForNew ddjThread3 = new DDJThreadForNew("reldd1", "bic", true,1,650, "nosamplex");
//        DDJThreadForNew ddjThread4 = new DDJThreadForNew("reldd2", "bic", true, 651,1700, "noconsider");
//        DDJThreadForNew ddjThread5 = new DDJThreadForNew("reldd2", "bic", true,651,1700, "nostart");
//        DDJThreadForNew ddjThread6 = new DDJThreadForNew("reldd2", "bic", true,651,1700, "nosamplex");
//        DDJThreadForNew ddjThread7 = new DDJThreadForNew("reldd3", "bic", true, 1701,1800, "noconsider");
//        DDJThreadForNew ddjThread8 = new DDJThreadForNew("reldd3", "bic", true,1701,1800,"nostart");
//        DDJThreadForNew ddjThread9 = new DDJThreadForNew("reldd3", "bic", true,1701,1800, "nosamplex");


//        DDJThread ddjThread1 = new DDJThread("prodd1", "bic", true, 1,300);
//        DDJThread ddjThread2 = new DDJThread("prodd2", "bic", true,301,650);
//        DDJThread ddjThread3 = new DDJThread("prodd3", "bic", true,651,1300);
//        DDJThread ddjThread4 = new DDJThread("prodd4", "bic", true,1301,1800);

//        DDJThread ddjThread2 = new DDJThread("prodd", "bic", true);

        DDJThreadForDefects4j ddjThread1 = new DDJThreadForDefects4j("ddmin", "defects4j", true);
        DDJThreadForDefects4j ddjThread2 = new DDJThreadForDefects4j("prodd", "defects4j", true);

        ddjThread1.start();
        Thread.sleep(10000); // Wait for 10 second
        ddjThread2.start();
        Thread.sleep(10000); // Wait for 10 second
//
//        DDJThreadForDiff ddjThread1 = new DDJThreadForDiff("ddmin", "diff", true);
//        ddjThread1.setName("diff_ddmin_true");
//        ddjThread1.start();
    }


}
