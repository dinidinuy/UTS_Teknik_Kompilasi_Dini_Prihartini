import sys
import re
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk

class Lexer:
    def __init__(self, source_code):
        self.source_code = source_code
        self.tokens = []
        self.errors = []

    def tokenize(self):
        token_specification = [
            ('KEYWORD',  r'\b(if|else|while|int|float|string|print)\b'),
            ('ID',       r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
            ('NUMBER',   r'\b\d+(\.\d+)?\b'),
            ('STRING',   r'"[^"]*"'),
            ('ASSIGN',   r'='),
            ('OP',       r'[+\-*/<>]=?|=='),
            ('DELIM',    r'[(),;{}]'),
            ('SKIP',     r'[ \t\n\r]+'),
            ('MISMATCH', r'.'),
        ]
        tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
        
        line_num = 1
        for mo in re.finditer(tok_regex, self.source_code):
            kind = mo.lastgroup
            value = mo.group(kind)
            if kind in ['KEYWORD', 'ID', 'NUMBER', 'STRING', 'ASSIGN', 'OP', 'DELIM']:
                self.tokens.append((kind, value, line_num))
            elif kind == 'SKIP':
                line_num += value.count('\n')
                continue
            elif kind == 'MISMATCH':
                self.errors.append(f"Lexical Error: Karakter tidak dikenal '{value}' pada baris {line_num}")
                line_num += value.count('\n')
        return self.tokens, self.errors


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return (None, None, -1)

    def eat(self, token_type):
        kind, val, line = self.current_token()
        if kind == token_type:
            self.pos += 1
        else:
            self.errors.append(f"Syntax Error: Diharapkan token tipe '{token_type}', ditemukan '{val}' ({kind}) pada baris {line}")

    def parse(self):
        while self.pos < len(self.tokens):
            kind, val, line = self.current_token()
            if kind is None:
                break
            if kind == 'KEYWORD' and val in ['int', 'float', 'string']:
                self.parse_declaration()
            elif kind == 'ID':
                self.parse_assignment()
            elif kind == 'KEYWORD' and val == 'print':
                self.parse_print()
            elif kind == 'KEYWORD' and val in ['if', 'while']:
                self.parse_control_flow()
            else:
                self.errors.append(f"Syntax Error: Pernyataan tidak valid '{val}' pada baris {line}")
                self.pos += 1
        return len(self.errors) == 0, self.errors

    def parse_declaration(self):
        self.eat('KEYWORD')
        self.eat('ID')
        kind, val, _ = self.current_token()
        if kind == 'ASSIGN':
            self.eat('ASSIGN')
            self.parse_expression()
        self.eat('DELIM')

    def parse_assignment(self):
        self.eat('ID')
        self.eat('ASSIGN')
        self.parse_expression()
        self.eat('DELIM')

    def parse_print(self):
        self.eat('KEYWORD')
        self.eat('DELIM')
        self.parse_expression()
        self.eat('DELIM')
        self.eat('DELIM')

    def parse_control_flow(self):
        self.eat('KEYWORD')
        self.eat('DELIM')
        self.parse_expression()
        self.eat('DELIM')
        self.eat('DELIM')
        while self.current_token()[1] != '}' and self.current_token()[0] is not None:
            self.pos += 1
        self.eat('DELIM')

    def parse_expression(self):
        kind, val, line = self.current_token()
        if kind in ['ID', 'NUMBER', 'STRING']:
            self.pos += 1
            next_kind, _, _ = self.current_token()
            if next_kind == 'OP':
                self.eat('OP')
                k2, v2, l2 = self.current_token()
                if k2 in ['ID', 'NUMBER']:
                    self.pos += 1
                else:
                    _ = l2
                    self.errors.append(f"Syntax Error: Operand tidak valid setelah operator pada baris {line}")
        else:
            self.errors.append(f"Syntax Error: Ekspresi tidak valid pada baris {line}")
            self.pos += 1


class SemanticAnalyzer:
    def __init__(self, tokens):
        self.tokens = tokens
        self.symbol_table = {}
        self.errors = []

    def analyze(self):
        i = 0
        while i < len(self.tokens):
            kind, val, line = self.tokens[i]
            if kind == 'KEYWORD' and val in ['int', 'float', 'string']:
                var_type = val
                if i + 1 < len(self.tokens) and self.tokens[i+1][0] == 'ID':
                    var_name = self.tokens[i+1][1]
                    if var_name in self.symbol_table:
                        self.errors.append(f"Semantic Error: Variabel '{var_name}' sudah dideklarasikan (Baris {line})")
                    else:
                        self.symbol_table[var_name] = var_type
                i += 2
            elif kind == 'ID':
                var_name = val
                if var_name not in self.symbol_table:
                    self.errors.append(f"Semantic Error: Variabel '{var_name}' digunakan sebelum deklarasi (Baris {line})")
                i += 1
            else:
                i += 1
        return len(self.errors) == 0, self.errors, self.symbol_table


class IntermediateCodeGenerator:
    def __init__(self, tokens):
        self.tokens = tokens

    def generate(self):
        ic_code = []
        temp_count = 1
        i = 0
        while i < len(self.tokens):
            kind, val, _ = self.tokens[i]
            if kind == 'KEYWORD' and val in ['int', 'float', 'string']:
                var_name = self.tokens[i+1][1]
                if i + 3 < len(self.tokens) and self.tokens[i+2][1] == '=':
                    val1 = self.tokens[i+3][1]
                    if i + 5 < len(self.tokens) and self.tokens[i+4][0] == 'OP':
                        op = self.tokens[i+4][1]
                        val2 = self.tokens[i+5][1]
                        t = f"t{temp_count}"
                        ic_code.append(f"{t} = {val1} {op} {val2}")
                        ic_code.append(f"{var_name} = {t}")
                        temp_count += 1
                        i += 7
                        continue
                    else:
                        ic_code.append(f"{var_name} = {val1}")
                        i += 5
                        continue
            i += 1
        if not ic_code:
            ic_code.append("; (Tidak ada kalkulasi kompleks untuk kode antara)")
        return ic_code


class CodeOptimizer:
    def __init__(self, ic_code):
        self.ic_code = ic_code

    def optimize(self):
        optimized = []
        for line in self.ic_code:
            match = re.match(r'(t\d+)\s*=\s*(\d+)\s*([\+\-\*\/])\s*(\d+)', line)
            if match:
                t, left, op, right = match.groups()
                try:
                    res = eval(f"{left} {op} {right}")
                    optimized.append(f"{t} = {res}")
                    continue
                except ZeroDivisionError:
                    pass
            optimized.append(line)
        return optimized


class TargetCodeGenerator:
    def __init__(self, optimized_ic):
        self.ic = optimized_ic

    def generate(self):
        assembly = []
        assembly.append(";")
        for line in self.ic:
            if "=" in line and not line.strip().startswith(";"):
                parts = line.split(";")[0].strip().split("=")
                dest = parts[0].strip()
                expr = parts[1].strip()
                assembly.append(f"MOV AX, {expr}")
                assembly.append(f"MOV {dest}, AX")
            else:
                assembly.append(line)
        return assembly


class CompilerLabApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Laboratorium Teknik Kompilasi")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.examples = {
            "1. Kalkulasi Aritmatika": "int x = 5;\nint y = 10;\nint z = x + y;\nprint(z);",
            "2. Constant Folding": "int a = 10;\nint b = 20;\nint c = a + b;\nprint(c);",
            "3. Float & String": "float suhu = 36.5;\nstring nama = \"Lab\";\nprint(suhu);",
            "4. Error Semantik": "int nilai = 90;\nprint(total);",
            "5. Error Sintaks": "int x = 10\nint y = 20;"
        }

        self.create_widgets()

    def create_widgets(self):
        header_frame = tk.Frame(self.root, bg="#2c3e50", padx=15, pady=10)
        header_frame.pack(fill=tk.X)

        title_label = tk.Label(header_frame, text="LABORATORIUM TEKNIK KOMPILASI", font=("Arial", 16, "bold"), fg="white", bg="#2c3e50")
        title_label.pack(side=tk.LEFT)

        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_pane, padding=5)
        main_pane.add(left_frame, weight=1)

        lbl_input = ttk.Label(left_frame, text="Editor Kode Sumber:", font=("Arial", 11, "bold"))
        lbl_input.pack(anchor=tk.W, pady=5)

        self.code_input = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, font=("Consolas", 11), height=22)
        self.code_input.pack(fill=tk.BOTH, expand=True, pady=5)
        self.code_input.insert(tk.END, self.examples["1. Kalkulasi Aritmatika"])

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        compile_btn = ttk.Button(btn_frame, text="Kompilasi", command=self.run_compilation)
        compile_btn.pack(side=tk.LEFT, padx=2)

        clear_btn = ttk.Button(btn_frame, text="Bersih", command=self.clear_editor)
        clear_btn.pack(side=tk.LEFT, padx=2)

        self.example_var = tk.StringVar()
        example_combo = ttk.Combobox(btn_frame, textvariable=self.example_var, values=list(self.examples.keys()), state="readonly", width=25)
        example_combo.pack(side=tk.RIGHT, padx=2)
        example_combo.set("Contoh...")
        example_combo.bind("<<ComboboxSelected>>", self.load_example)

        right_frame = ttk.Frame(main_pane, padding=5)
        main_pane.add(right_frame, weight=1)

        lbl_output = ttk.Label(right_frame, text="Panel Hasil Analisis:", font=("Arial", 11, "bold"))
        lbl_output.pack(anchor=tk.W, pady=5)

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)

        self.tab_lexical = self.create_tab("1. Lexical")
        self.tab_syntax = self.create_tab("2. Syntax")
        self.tab_semantic = self.create_tab("3. Semantic")
        self.tab_ic = self.create_tab("4. Intermediate")
        self.tab_opt = self.create_tab("5. Optimization")
        self.tab_target = self.create_tab("6. Target Code")

    def create_tab(self, name):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=name)
        txt = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=("Consolas", 10), height=20)
        txt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        txt.config(state=tk.DISABLED)
        return txt

    def set_tab_content(self, tab_widget, content):
        tab_widget.config(state=tk.NORMAL)
        tab_widget.delete("1.0", tk.END)
        tab_widget.insert(tk.END, content)
        tab_widget.config(state=tk.DISABLED)

    def load_example(self, event):
        selected_name = self.example_var.get()
        if selected_name in self.examples:
            self.code_input.delete("1.0", tk.END)
            self.code_input.insert(tk.END, self.examples[selected_name])

    def clear_editor(self):
        self.code_input.delete("1.0", tk.END)
        for tab in [self.tab_lexical, self.tab_syntax, self.tab_semantic, self.tab_ic, self.tab_opt, self.tab_target]:
            self.set_tab_content(tab, "")

    def run_compilation(self):
        source = self.code_input.get("1.0", tk.END).strip()
        if not source:
            messagebox.showwarning("Peringatan", "Kode sumber kosong!")
            return

        lexer = Lexer(source)
        tokens, lex_errors = lexer.tokenize()
        
        lex_output = "DAFTAR TOKEN:\n"
        for t in tokens:
            lex_output += f"Tipe: {t[0]:<10} | Nilai: {t[1]:<15} | Baris: {t[2]}\n"
        if lex_errors:
            lex_output += "\nERROR:\n" + "\n".join(lex_errors)
        self.set_tab_content(self.tab_lexical, lex_output)

        if lex_errors:
            for tab in [self.tab_syntax, self.tab_semantic, self.tab_ic, self.tab_opt, self.tab_target]:
                self.set_tab_content(tab, "Dibatalkan.")
            return

        parser = Parser(tokens)
        syntax_ok, syn_errors = parser.parse()
        
        syn_output = "STATUS PARSING:\n"
        if syntax_ok:
            syn_output += "Sintaks valid.\n"
        else:
            syn_output += "\n".join(syn_errors)
        self.set_tab_content(self.tab_syntax, syn_output)

        if not syntax_ok:
            for tab in [self.tab_semantic, self.tab_ic, self.tab_opt, self.tab_target]:
                self.set_tab_content(tab, "Dibatalkan.")
            return

        semantic = SemanticAnalyzer(tokens)
        semantic_ok, sem_errors, symbol_table = semantic.symbol_table_check if hasattr(semantic, 'symbol_table_check') else semantic.analyze()

        sem_output = "TABEL SIMBOL:\n"
        for var, vtype in symbol_table.items():
            sem_output += f"Variabel: {var:<10} | Tipe: {vtype}\n"
        
        sem_output += "\nSTATUS SEMANTIK:\n"
        if semantic_ok:
            sem_output += "Semantik valid.\n"
        else:
            sem_output += "\n".join(sem_errors)
        self.set_tab_content(self.tab_semantic, sem_output)

        if not semantic_ok:
            for tab in [self.tab_ic, self.tab_opt, self.tab_target]:
                self.set_tab_content(tab, "Dibatalkan.")
            return

        ic_gen = IntermediateCodeGenerator(tokens)
        ic_code = ic_gen.generate()
        self.set_tab_content(self.tab_ic, "\n".join(ic_code))

        optimizer = CodeOptimizer(ic_code)
        opt_code = optimizer.optimize()
        self.set_tab_content(self.tab_opt, "\n".join(opt_code))

        target_gen = TargetCodeGenerator(opt_code)
        target_code = target_gen.generate()
        self.set_tab_content(self.tab_target, "\n".join(target_code))


def run_automated_tests():
    app_tests = [
        ("Kalkulasi", "int x = 5;\nint y = 10;\nint z = x + y;\nprint(z);"),
        ("Folding", "int a = 10;\nint b = 20;\nint c = a + b;\nprint(c);"),
        ("Float", "float suhu = 36.5;\nstring nama = \"Lab\";\nprint(suhu);"),
        ("Semantik", "int nilai = 90;\nprint(total);"),
        ("Sintaks", "int x = 10\nint y = 20;")
    ]

    for title, code in app_tests:
        lexer = Lexer(code)
        tokens, l_err = lexer.tokenize()
        if not l_err:
            parser = Parser(tokens)
            ok_syn, _ = parser.parse()
            if ok_syn:
                sem = SemanticAnalyzer(tokens)
                ok_sem, _, _ = sem.analyze()
                if ok_sem:
                    ic = IntermediateCodeGenerator(tokens).generate()
                    opt = CodeOptimizer(ic).optimize()
                    _ = TargetCodeGenerator(opt).generate()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_automated_tests()
    else:
        root = tk.Tk()
        app = CompilerLabApp(root)
        root.mainloop()
