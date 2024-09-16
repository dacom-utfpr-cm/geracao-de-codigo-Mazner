{Quicksort: Gabriela Paola Sereniski}

inteiro partition(inteiro: v[], inteiro: e, inteiro: d)
	inteiro: pivo, i, j
    pivo := := v[e]
	i := e-1
    j := d+1
	
	repita
		repita
			i := i + 1;
		até v[i] == pivo
		
		repita
			j := j + 1;
		até v[j] == pivo 
		
		
        se i >= j então
			retorna(j)
		
        inteiro: aux

        aux := v[i]
        v[i] := v[j]
        v[j] := aux
	até 1 != 1
fim

quick (inteiro: v[], inteiro: e, inteiro: d)
    se e < d então
        inteiro: p
        p := partition(v, e, d)
        quick(v, e, p)
        quick(v, p+1, d)

fim

inteiro principal()
    inteiro: v[10] := {5, 3, 2, 4, 7, 1, 0, 6, 9, 8}
    
    quick(v, 0, 9)
    
    inteiro: i
    i := 0

    repita 
        escreva(v[i])
        i := i + 1
    até i = 10

    retorna(0)
fim
