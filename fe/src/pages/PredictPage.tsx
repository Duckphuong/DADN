import React from 'react';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import Predict from '../components/Predict';

export default function PredictPage() {
    return (
        <div className="min-h-screen bg-linear-to-br from-cyan-50 via-blue-50 to-blue-100">
            <Header />

            {/* <main className="max-w-400 mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <Predict />
            </main> */}
            <Predict />

            <Footer />
        </div>
    );
}
