import java.util.Scanner;

public class Main {
    public static void main(final String[] args) {
        final var sc = new Scanner(System.in);
        int a, b;
        while (sc.hasNext()) {
            a = sc.nextInt();
            b = sc.nextInt();
            System.out.println(a + b);
        }
        sc.close();
    }
}