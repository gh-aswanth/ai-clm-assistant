import Swal from 'sweetalert2'

export const toast = (title, icon = 'success') =>
  Swal.fire({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 2500,
    timerProgressBar: true,
    icon,
    title,
  })

export const swalError = (text, title = 'Error') =>
  Swal.fire({ title, text, icon: 'error' })

export const swalInfo = (text, title = '') =>
  Swal.fire({ title, text, icon: 'info' })

export const swalConfirm = async (text, title = 'Are you sure?', confirmText = 'Yes') => {
  const result = await Swal.fire({
    title,
    text,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#ef4444',
    cancelButtonColor: '#6b7280',
    confirmButtonText: confirmText,
    cancelButtonText: 'Cancel',
  })
  return result.isConfirmed
}
