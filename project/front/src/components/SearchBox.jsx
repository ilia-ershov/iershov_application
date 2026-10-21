export default function SearchBox({ value, onChange }) {
  return (
    <input
      type="search"
      className="search"
      placeholder="Поиск по адресу или сервису"
      aria-label="Поиск по адресу или сервису"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  )
}
