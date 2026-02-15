export default function LoadingSkeleton({ count = 4 }) {
    return (
        <div className="skeleton-grid">
            {Array.from({ length: count }).map((_, i) => (
                <div className="skeleton-tile" key={i} style={{ animationDelay: `${i * 0.1}s` }}>
                    <div className="skeleton-avatar" />
                    <div className="skeleton-lines">
                        <div className="skeleton-line" />
                        <div className="skeleton-line" />
                        <div className="skeleton-line" />
                    </div>
                </div>
            ))}
        </div>
    );
}
