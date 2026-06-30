| Command       | Arguments          | Answer  | Category | Description                                          |
| ------------- | ------------------ | ------- | -------- | ---------------------------------------------------- |
| `bufNoArgs`   | —                  | OK      | buffered | Buffered command with no arguments.                  |
| `bufAllTypes` | x ch flag sz color | OK      | buffered | Buffered command exercising every numeric arg type.  |
| `bufOptional` | a [b]              | OK      | buffered | Buffered command with an optional defaulted arg.     |
| `bufText`     | <text>             | OK      | buffered | Buffered raw-rest text; supports \n escapes.         |
| `qBounds`     | x <s>              | a b c d | query    | Query with a trailing string returning an int tuple. |
| `qValue`      | —                  | int     | query    | Query returning a single int.                        |
| `ctlVoid`     | —                  | —       | control  | Control command with no response.                    |
| `btnRead`     | [ms]               | string  | button   | Button command returning a string.                   |