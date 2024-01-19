// JAVASCRIPT

// CAMPOS DE TRANSFERENCIA
function toggleFields() {
    var operacao = document.getElementById('operacao').value;
    var destinoFields = document.getElementById('destinoFields');
    var destinoNumeroInput = document.getElementById('destino_numero');

    destinoFields.style.display = operacao === 'transferencia' ? 'block' : 'none';
    destinoNumeroInput.required = operacao === 'transferencia';
}

/*

// BANNER COM BLUR
window.addEventListener('scroll', function() {
    // ENCONTRA A POSIÇÃO Y = VERTICAL
    var scrollPosition = window.scrollY || document.documentElement.scrollTop;
    // CALCULA O VALOR CONFORME O SCROLL, E DEFINE 10 COMO MINIMO
    var blurValue = Math.min(scrollPosition / 10, 10);
    // APLICA
    document.querySelector('.blurable').style.filter = 'translateY(' + blurValue + 'px)';
});

*/

// DESATIVAR LOTE
$(document).ready(function () {
    $('#produto').on('change', function () {
        // SELECT2 CONTÉM 'VINHO' ?
        var isVinhoSelected = $(this).val().toLowerCase().includes('vinho');

        // SELECIONA INPUT-LOTE
        var inputLote = $('input[name="lote"]');

        // TOGGLER
        if (isVinhoSelected) {
            // INPUT-LOTE -> READ-ONLY
            inputLote.prop('readonly', true);
            inputLote.val('VINHO');
        }
        else {
            // LOTE -> WRITE
            inputLote.prop('readonly', false);
            inputLote.val('');
        }
    });
});



// ANIMAÇÃO DE ENTRADA
document.addEventListener("DOMContentLoaded", function() {
    var elementToAnimate = document.getElementById("destinoFields");
    elementToAnimate.classList.add("fade-in-from-top");
});


// HEADER POP-UP
window.addEventListener('scroll', function() {
    // ENCONTRA A POSIÇÃO Y = VERTICAL
    var scrollPosition = window.scrollY || document.documentElement.scrollTop;

    if (scrollPosition > 50) {
        // CALCULA O VALOR CONFORME O SCROLL (10 COMO MINIMO)
        var blurValue = Math.min(scrollPosition / 10, 10);
        // APLICA
        document.querySelector('header.main-header').classList.add('scrolled');
    } else {
        document.querySelector('header.main-header').classList.remove('scrolled');
    }
});


// FUNÇÃO PARA CAPS
function capitalizeTexto() {

    var inputsTexto = document.querySelectorAll('input[type="text"]');
    inputsTexto.forEach(function(input) {
        input.addEventListener('input', function() {

            this.value = this.value.toUpperCase();
        });
    });
}


// SELECT2 (CAIXA DE PESQUISA)
$(document).ready(function() {
  $('.select2').select2();
});


// VALIDAÇÃO DE LETRAS NO CAPS P/ INPUTS
window.onload = capitalizeTexto;
