$(document).ready(function() {
  $('#freq-dist').DataTable({
    order: [[3, 'desc']],
    pageLength: 25,
    columnDefs: [
      { orderable: false, targets: [2, 4] }
    ]
  });
});
