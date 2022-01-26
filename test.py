
# harmonicCent similarity 1 - 2:  0.999732734153876
# eigenvectorCent similarity 1 - 2:  0.9841860066035627
# closenessCent similarity 1 - 2:  0.9999712631204428
# betweennessCent similarity 1 - 2:  0.9997612100382818

code1 = '''void MyFNatoi (const char *str, int *value) {
    if (value == NULL)
        return;
    *value = 0;
    if (str != NULL) {
        int negative = 0;
        if (*str == '-') {
            negative = 1;
            str++;
        }
        while (*str && isdigit (*str)) {
            *value = (*value * 10) + (*str++ - '0');
        }
        if (negative)
            *value *= -1;
    }
}'''

code2 = '''void MyFNatoi (char *numArray, int *value) {
    int i;
    *value = 0;
    for (i = 0; i < 10 && numArray[i] != 0; i++) {
        if (numArray[i] >= Zero && numArray[i] <= Nine) {
            *value = *value * 10 + (numArray[i] - Zero);
        }
    }
}'''

text1 = r"""
void main() {
    int x; 
    foo(1,3);
    foo1(4);
    x = 1;
    foo2(4,10,3);
    foo3("xxx");
}
"""

text2 = r"""
void main() {
    int x, y; 
    foo(x,y);
    x = 1;
    foo2(4,10,3);
    foo3("xxx");
}
"""

text3 = r"""
int max(int x,int y)
{
    int t;
    t = x>y?x:y;
    return t;
}

int main()
{
    int maxs;
    maxs = max(2,3);
    printf("%d",maxs);
}
"""
