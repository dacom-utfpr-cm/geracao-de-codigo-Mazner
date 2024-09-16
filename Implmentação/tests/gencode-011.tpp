{Repita, Leia e Escreva}

inteiro: n
inteiro: soma

inteiro principal()

	leia(n)

	soma := 0
	repita
		soma := soma + n
		n := n - 1
	até n = 0

	escreva(soma)

	retorna(0)
fim
