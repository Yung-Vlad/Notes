import './Main.scss';
import React from 'react';

function Main() {
    // Function to handle the button click
    const handleStartClick = async () => {
        try {
            const response = await fetch('http://localhost:8000/users/check-session', {
                method: 'GET',
            });

            if (response.ok) {
                const data = await response.json();
                alert(`Success: ${data.message}`); // Display success message
            } else {
                const errorData = await response.json();
                alert(`Error: ${errorData.detail}`); // Display error message
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while connecting to the server.');
        }
    };

    return (
        <div className='container'>
            <h1 className='h1'>Your notes, locked and loaded</h1>

            <h3 className='h3 properties'>Fast. Secure. Yours</h3>

            {/* Attach the function to the button's onClick */}
            <button className='start button' onClick={handleStartClick}>
                Start Writing
            </button>

            <div className="property-cards">
                <div className="card">
                    <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#FFFFFF">
                        <path d="M240-80q-33 0-56.5-23.5T160-160v-400q0-33 23.5-56.5T240-640h40v-80q0-83 58.5-141.5T480-920q83 0 141.5 58.5T680-720v80h40q33 0 56.5 23.5T800-560v400q0 33-23.5 56.5T720-80H240Zm0-80h480v-400H240v400Zm240-120q33 0 56.5-23.5T560-360q0-33-23.5-56.5T480-440q-33 0-56.5 23.5T400-360q0 33 23.5 56.5T480-280ZM360-640h240v-80q0-50-35-85t-85-35q-50 0-85 35t-35 85v80ZM240-160v-400 400Z" />
                    </svg>
                    <h4 className='card-heading h4'>Secure</h4>
                </div>
                <div className="card">
                    <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#FFFFFF">
                        <path d="m422-232 207-248H469l29-227-185 267h139l-30 208ZM320-80l40-280H160l360-520h80l-40 320h240L400-80h-80Zm151-390Z" />
                    </svg>
                    <h4 className='card-heading h4'>Fast</h4>
                </div>
                <div className="card">
                    <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#FFFFFF">
                        <path d="M80-160v-120h80v-440q0-33 23.5-56.5T240-800h600v80H240v440h240v120H80Zm520 0q-17 0-28.5-11.5T560-200v-400q0-17 11.5-28.5T600-640h240q17 0 28.5 11.5T880-600v400q0 17-11.5 28.5T840-160H600Zm40-120h160v-280H640v280Zm0 0h160-160Z" />
                    </svg>
                    <h4 className='card-heading h4'>Cross-platform</h4>
                </div>
            </div>

            <a href="#">Some link</a>
        </div>
    );
}

export default Main;