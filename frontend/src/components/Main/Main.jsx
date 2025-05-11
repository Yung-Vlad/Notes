import './Main.scss';

function Main() {
    return (  
        <div className='container'>
            <h1>Your notes, locked and loaded</h1>

            <h2>Fast. Secure. Yours</h2>

            <button>Start Writing</button>

            <div className="properties">
                <div className="card">Secure</div>
                <div className="card">Fast</div>
                <div className="card">Cross-platform</div>
            </div>

        </div>
    );
}

export default Main;