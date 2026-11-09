//ogni ordine è agganciato a un cliente realmente 
//esistente nel database.

use('ecommerce_tesi_db');

db.order.aggregate([
  { $limit: 1 }, // Prende il primo ordine per fare un test 
  {
//"Prendi quel codice cid che vedi nell'ordine, 
//vai nella collezione dei clienti (customer), 
//cerca il cliente che ha quell'esatto _id e portami 
//indietro la sua scheda completa."
    $lookup: {
      from: "customer",           // Cerca nella collezione dei clienti
      localField: "CUSTOMER.cid", // usiamo la dot notation!
      foreignField: "_id",        // La chiave primaria nella collezione customer
      as: "cliente_associato"     // Nome del campo di output
    }
  }
]);