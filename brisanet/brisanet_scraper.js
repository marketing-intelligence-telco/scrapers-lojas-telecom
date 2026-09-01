(function() {
    const rawData = JSON.parse(_pageData);
    let results = [];

    function search(obj) {
        if (Array.isArray(obj)) {
            // Nova Assinatura: Verifica se o obj[0] é um ID hexadecimal e obj[1] tem as coordenadas
            if (obj.length >= 6 && typeof obj[0] === 'string' && /^[0-9A-F]{10,}$/i.test(obj[0]) && Array.isArray(obj[1]) && Array.isArray(obj[5])) {

                let id = obj[0];
                let lat = "";
                let lng = "";

                try {
                    // Puxa as coordenadas da nova localização descoberta
                    lat = obj[1][0][0][0];
                    lng = obj[1][0][0][1];
                } catch(e) {}

                // Função interna para garimpar as variáveis exatas dentro desse ponto
                function findAttr(node, key) {
                    let result = "";
                    function dig(n) {
                        if (Array.isArray(n)) {
                            // Se encontrar a etiqueta (ex: "Telefone") e o valor do lado
                            if (n[0] === key && Array.isArray(n[1])) {
                                result = n[1][0];
                                return;
                            }
                            n.forEach(dig);
                        }
                    }
                    dig(node);
                    return result;
                }

                let nome = findAttr(obj[5], "nome") || "";
                let endereco = findAttr(obj[5], "Endereço") || "";
                let telefone = findAttr(obj[5], "Telefone") || "";
                let tipoCadastro = findAttr(obj[5], "Tipo do Cadastro") || "";

                // --- INTELIGÊNCIA PARA FATIAR O ENDEREÇO ---
                // 1. Extrai o CEP (Procura pelo padrão 00000-000)
                let cep = (endereco.match(/\d{5}-\d{3}/) || [""])[0];

                // 2. Extrai UF (Procura por " - CE", " / PB", etc)
                let ufMatch = endereco.match(/[-/]\s*([A-Z]{2})\b/);
                let uf = ufMatch ? ufMatch[1] : "";

                // 3. Extrai Cidade (Pega o texto que vem antes da UF e tenta isolar a cidade)
                let cidade = "";
                if (ufMatch && ufMatch.index > 0) {
                    let textBeforeUF = endereco.substring(0, ufMatch.index);
                    let parts = textBeforeUF.split(/[,\\-]/); // Corta onde tem vírgula ou traço
                    cidade = parts[parts.length - 1].trim(); // Pega a última parte (geralmente a cidade)
                }

                // Limpa quebras de linha e aspas do endereço para não quebrar o CSV
                let enderecoLimpo = endereco.replace(/"/g, "'").replace(/\n/g, " ");

                if (lat && lng) {
                    results.push({
                        id, nome, cidade, uf, endereco: enderecoLimpo, cep, telefone, tipoCadastro, lat, lng
                    });
                }
            }

            // Continua cavando os outros nós
            obj.forEach(search);
        }
    }

    search(rawData);

    if (results.length === 0) {
        console.error("Nada encontrado com a nova estrutura.");
    } else {
        let csv = "ID;Nome da Loja;Cidade;UF;Endereço;CEP;Telefone;Tipo de Cadastro;Latitude;Longitude\n";
        
        results.forEach(r => {
            // CORREÇÃO: Transforma os pontos das coordenadas em vírgulas para o padrão Excel BR
            let latBR = r.lat.toString().replace('.', ',');
            let lngBR = r.lng.toString().replace('.', ',');

            csv += `"${r.id}";"${r.nome}";"${r.cidade}";"${r.uf}";"${r.endereco}";"${r.cep}";"${r.telefone}";"${r.tipoCadastro}";"${latBR}";"${lngBR}"\n`;
        });

        copy(csv);
        console.log("--------------------------------------------");
        console.log(`SUCESSO MÁXIMO! Encontrados ${results.length} registros com todos os dados.`);
        console.log("Os dados já estão no seu Clipboard (Ctrl+C automático).");
        console.log("Vá até a célula A1 do Excel e cole (Ctrl+V)! Agora com coordenadas padrão BR.");
        console.log("--------------------------------------------");
    }
})();