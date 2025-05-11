import './Main.scss';

function Main() {
    return (
        <div className='container'>
            <h1 className='h1'>Your notes, locked and loaded</h1>

            <h3 className='h3 properties'>Fast. Secure. Yours</h3>

            <button className='start'>Start Writing</button>

            <div className="property-cards">
                <div className="card">
                    <h4 className='card-heading h4'>
                        Secure
                    </h4>
                </div>
                <div className="card">
                    <h4 className='card-heading h4'>
                        Fast
                    </h4>
                </div>
                <div className="card">
                    <h4 className='card-heading h4'>
                        Cross-platform
                    </h4>
                </div>
            </div>

            <a href="#">Some link</a>

        </div>
    );
}

export default Main;