#include <iostream>
#include <vector>
#include <cmath>
#include <iomanip>
#include <string>

using namespace std;

// 計算變動現金流的期末價值
double calculate(const vector<double>& monthly_P, int T, double r) {
    double sum = 0.0;
    for (int t = 1; t <= T; t++) {
        // 第 t 個月的錢會滾存 (T - t + 1) 期
        sum += monthly_P[t - 1] * pow(1 + r, T - t + 1);
    }
    return sum;
}

double findIRR(const vector<double>& monthly_P, int T, double P_final) {
    double left = -0.999, right = 1.0;
    double mid;

    // 自動擴展右邊界
    while (calculate(monthly_P, T, right) < P_final) {
        right *= 2;
        if (right > 1e10) break;
    }

    for (int i = 0; i < 100; i++) {
        mid = (left + right) / 2.0;
        double value = calculate(monthly_P, T, mid);

        if (value > P_final)
            right = mid;
        else
            left = mid;
    }
    return mid;
}

int main() {
    int T;
    double P_final;

    cout << "1. 請輸入總月數 (T): ";
    if (!(cin >> T)) return 0;

    vector<double> monthly_P(T);
    cout << "2. 請「一次性貼上」或輸入這 " << T << " 個月的金額 (以空白或 Enter 分隔): " << endl;

    // 這裡會一次讀取 T 個數字，你可以直接從 Excel 複製一列數字貼過來
    for (int i = 0; i < T; i++) {
        cin >> monthly_P[i];
    }

    cout << "3. 請輸入最終期末總價值 (P_final): ";
    cin >> P_final;

    double r = findIRR(monthly_P, T, P_final);

    cout << "\n====================================" << endl;
    cout << "  計算結果" << endl;
    cout << "====================================" << endl;
    cout << fixed << setprecision(5);
    cout << "月回報率 (IRR)     : " << r << endl;
    cout << "年化報酬率 (單利)  : " << r * 12 * 100 << "%" << endl;
    cout << "年化報酬率 (複利)  : " << (pow(1 + r, 12) - 1) * 100 << "%" << endl;
    cout << "====================================" << endl;

    return 0;
}