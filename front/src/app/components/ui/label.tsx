interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
    children: React.ReactNode
  }
  
  export function Label({ className, children, ...props }: LabelProps) {
    return (
      <label
        className={`text-sm font-medium leading-none ${className}`}
        {...props}
      >
        {children}
      </label>
    )
  }