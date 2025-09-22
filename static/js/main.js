// --- 1. Cesiumの初期設定 ---
Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI2ODNkYWVjYi01ZTliLTQ2MTctYmZiOS1kNDQ3MTIxZjYzYjYiLCJpZCI6MzIxOTcyLCJpYXQiOjE3NTI2NTYzOTd9.m81UdYhfay_9fi85IjYCKQN7QC9lO8VQN25qV7LyQ7k';

const viewer = new Cesium.Viewer('cesiumContainer', {
    infoBox: false,
    selectionIndicator: false,
    imageryProvider: new Cesium.OpenStreetMapImageryProvider({
        url: 'https://tile.openstreetmap.org/'
    }),
    sceneModePicker: false, // 2D/3D切り替えボタンを表示
    baseLayerPicker: false,
    timeline: false,
    animation: false,
});

// 3Dタイルセットを後から操作できるように、変数として保持
let photorealisticTileset;

// Google 3D Tilesを読み込み
(async () => {
    try {
        photorealisticTileset = await Cesium.createGooglePhotorealistic3DTileset();
        viewer.scene.primitives.add(photorealisticTileset);

    } catch (error) {
        console.error(`3Dタイルの読み込みエラー: ${error}`);
    }
})();

// 【修正点】カメラの初期位置を呉市に変更
viewer.camera.setView({
    destination: Cesium.Cartesian3.fromDegrees(132.55, 34.243, 500), // 
    orientation: {
        heading: Cesium.Math.toRadians(0.0),
        pitch: Cesium.Math.toRadians(-45.0),
    },
});


// --- 2. データ取得とピンの表示 ---
let allEntities = []; // 全てのエンティティを保持する配列
const pinBuilder = new Cesium.PinBuilder();
pinBuilder.fromText("A", Cesium.Color.RED, 64);


// ステータスに応じた色を返すヘルパー関数
function getStatusColor(ownerStatus) {
    // Excelファイルに 'status' 列がない場合は、ここで調整が必要
    switch (ownerStatus) {
        case '私道': return Cesium.Color.ORANGE;
        case '認定市道': return Cesium.Color.LIMEGREEN;
        case '私有地': return Cesium.Color.DODGERBLUE;
        default: return Cesium.Color.ROYALBLUE; // デフォルトの色
    }
}



async function loadCustomData() {
    try {
        const response = await fetch('/api/locations'); // Python側のAPIパス
        const locations = await response.json();

        locations.forEach(data => {
            if (data.longitude && data.latitude) {
                const entity = viewer.entities.add({
                    position: Cesium.Cartesian3.fromDegrees(data.longitude, data.latitude),
                    billboard: {
                        image: pinBuilder.fromColor(getStatusColor(data.ownerStatus), 48).toDataURL(),
                        verticalOrigin: Cesium.VerticalOrigin.TOP,
                        disableDepthTestDistance: Number.POSITIVE_INFINITY, 
                        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND 
                    
                        

                    },
                    properties: data 
                });
                allEntities.push(entity);
            }
        });
    } catch (error) {
        console.error('カスタムデータの読み込みエラー:', error);
    }
}



document.addEventListener('DOMContentLoaded', () => {
    // HTML要素の取得
    const sidebar = document.getElementById('info-sidebar');
    const sidebarContent = document.getElementById('sidebar-content');
    const closeSidebarBtn = document.getElementById('close-sidebar-btn');
    const toggle3dBtn = document.getElementById('toggle-3d-btn');
    const filterButtons = document.querySelectorAll('.filter-btn'); // ここで定義

    // 地図上のクリックイベントを処理
    viewer.screenSpaceEventHandler.setInputAction(function onLeftClick(movement) {
        const pickedObject = viewer.scene.pick(movement.position);
        if (Cesium.defined(pickedObject) && Cesium.defined(pickedObject.id)) {
            const entity = pickedObject.id;
            if (entity.billboard) {
                const data = entity.properties.getValue(viewer.clock.currentTime);   
                
                // サイドバーに情報を表示
                sidebarContent.innerHTML = `
                    <h2>${data.整備名 || '名称未設定'}</h2>
                    ${data.image_url ? `<img src="${data.image_url}" alt="${data.整備名}">` : ''}
                    
                    <p><strong>目的:</strong> ${data.目的 || '情報なし'}</p>
                    <p><strong>発意:</strong> ${data.発意 || '情報なし'}</p>
                    <p><strong>実行:</strong> ${data.実行 || '情報なし'}</p>
                    <p><strong>費用:</strong> ${data.費用 || '情報なし'}</p>
                    <p><strong>契機:</strong> ${data.契機 || '情報なし'}</p>
                    <p><strong>時期:</strong> ${data.時期 || '情報なし'}</p>
                    <p><strong>所有:</strong> ${data.所有 || '情報なし'}</p>
                    <p><strong>管理:</strong> ${data.管理 || '情報なし'}</p>
                    <p><strong>備考:</strong> ${data.備考 || '情報なし'}</p>
                `;
                sidebar.classList.add('sidebar-visible');

                // 【新機能】クリックしたエンティティにズーム
                viewer.flyTo(entity, {
                    duration: 1.5, // 1.5秒かけて移動
                    offset: new Cesium.HeadingPitchRange(
                        Cesium.Math.toRadians(0.0),   // 正面から見る
                        Cesium.Math.toRadians(-30.0), // 少し上から見下ろす
                        50                          // 700mの距離まで近づく
                    )
                });
            } 
        } else {
            // 何もない場所をクリックしたらサイドバーを隠す
            sidebar.classList.remove('sidebar-visible');
        }
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

    // 閉じるボタンのイベント
    closeSidebarBtn.addEventListener('click', () => {
        sidebar.classList.remove('sidebar-visible');
    });

    // フィルターボタンのイベント (エラーが出ていた部分)
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            const status = button.getAttribute('data-status');
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            allEntities.forEach(entity => {
                const entityOwnerStatus = entity.properties.getValue(viewer.clock.currentTime).所有;
                if (status === 'all' || entityOwnerStatus === status) {
                    entity.show = true;
                } else {
                    entity.show = false;
                }
            });
        });
    });

    

    // ページロード時にデータを読み込む
    loadCustomData();
});

// main.js の toggle3dBtn のイベントリスナーを置き換える

toggle3dBtn.addEventListener('change', (event) => {
    // 3Dタイルが読み込まれていない場合は何もしない
    if (!photorealisticTileset) {
        return;
    }

    const is3DEnabled = event.target.checked;

    // 3D建物の表示/非表示
    photorealisticTileset.show = is3DEnabled;
    viewer.scene.globe.enableLighting = is3DEnabled;

    // 3D/2Dビューの切り替え
    if (is3DEnabled) {
        // --- 3Dビューに戻す ---
        
        // 1. 地球の照明を有効にし、地形の陰影をリアルにする
        viewer.scene.globe.enableLighting = true;
        
        // 2. カメラを斜め上からの視点に戻す
        viewer.camera.flyTo({
            orientation: {
                heading: viewer.camera.heading, // 現在のカメラの向きを維持
                pitch: Cesium.Math.toRadians(-45.0), // 斜め45度の視点
                roll: 0.0
            },
            duration: 1.0 // 1秒かけてスムーズに移動
        });

    } else {
        // --- 2Dビューに切り替える ---

        // 1. 地球の照明を無効にし、フラットな2Dマップのように見せる
        viewer.scene.globe.enableLighting = false;

        // 2. カメラを真上からの視点（2Dマップ風）に移動
        viewer.camera.flyTo({
            orientation: {
                heading: Cesium.Math.toRadians(0.0), // 北を真上にする
                pitch: Cesium.Math.toRadians(-90.0), // 真上から見下ろす
                roll: 0.0
            },
            duration: 1.0
        });
    }
});